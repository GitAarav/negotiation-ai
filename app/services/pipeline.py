from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.errors import PipelineError
from app.models import PipelineResponse
from app.repositories import InteractionRepository, UserPreferenceRepository
from app.services.documents import DocumentService
from app.services.language import LanguageService
from app.services.negotiation import NegotiationClient
from app.services.speech import SpeechToTextService
from app.services.translation import Translator
from app.services.tts import TextToSpeechService


class PipelineService:
    def __init__(
        self,
        *,
        temp_upload_dir: Path,
        language_service: LanguageService,
        translator: Translator,
        negotiation_client: NegotiationClient,
        tts_service: TextToSpeechService,
        speech_service: SpeechToTextService,
        document_service: DocumentService,
        interaction_repository: InteractionRepository,
        preference_repository: UserPreferenceRepository,
        enable_side_by_side_text: bool,
        default_output_language: str,
    ) -> None:
        self.temp_upload_dir = temp_upload_dir
        self.language_service = language_service
        self.translator = translator
        self.negotiation_client = negotiation_client
        self.tts_service = tts_service
        self.speech_service = speech_service
        self.document_service = document_service
        self.interaction_repository = interaction_repository
        self.preference_repository = preference_repository
        self.enable_side_by_side_text = enable_side_by_side_text
        self.default_output_language = default_output_language

    async def process_text(
        self,
        *,
        user_id: str,
        text: str,
        channel: str,
        source_language: str | None,
        preferred_output_language: str | None,
        include_audio: bool,
    ) -> PipelineResponse:
        source_lang = self._resolve_source_language(text, source_language)
        target_lang = self._resolve_target_language(user_id, preferred_output_language)
        english_input = text
        translation_confidence = None

        if source_lang != "en":
            translation = await self.translator.translate(
                text,
                source_language=source_lang,
                target_language="en",
            )
            english_input = translation.translated_text
            translation_confidence = translation.confidence

        negotiation_response = await self.negotiation_client.submit(english_input)
        localized_text = negotiation_response.suggestion

        if target_lang != "en":
            outbound = await self.translator.translate(
                negotiation_response.suggestion,
                source_language="en",
                target_language=target_lang,
            )
            localized_text = outbound.translated_text
            translation_confidence = outbound.confidence or translation_confidence

        audio = await self.tts_service.synthesize(localized_text, target_lang) if include_audio else None
        interaction = self.interaction_repository.create(
            {
                "user_id": user_id,
                "channel": channel,
                "source_language": source_lang,
                "target_language": target_lang,
                "original_text": text,
                "english_text": english_input,
                "negotiation_response_en": negotiation_response.suggestion,
                "localized_response_text": localized_text,
            }
        )

        side_by_side = None
        if self.enable_side_by_side_text:
            side_by_side = {
                "original_text": text,
                "english_input": english_input,
                "english_response": negotiation_response.suggestion,
                "localized_response_text": localized_text,
            }

        return PipelineResponse(
            interaction_id=interaction.id,
            user_id=user_id,
            channel=channel,  # type: ignore[arg-type]
            source_language=source_lang,
            target_language=target_lang,
            original_text=text,
            english_input=english_input,
            english_response=negotiation_response.suggestion,
            localized_response_text=localized_text,
            localized_response_audio_base64=audio,
            translation_confidence=translation_confidence,
            side_by_side=side_by_side,
        )

    async def process_speech(
        self,
        *,
        user_id: str,
        audio: UploadFile,
        preferred_output_language: str | None,
        include_audio: bool,
    ) -> PipelineResponse:
        file_path = await self._persist_upload(audio)
        transcript = await self.speech_service.transcribe(file_path)
        return await self.process_text(
            user_id=user_id,
            text=transcript.transcript,
            channel="speech",
            source_language=transcript.detected_language,
            preferred_output_language=preferred_output_language,
            include_audio=include_audio,
        )

    async def process_document(
        self,
        *,
        user_id: str,
        document: UploadFile,
        preferred_output_language: str | None,
        include_audio: bool,
    ) -> PipelineResponse:
        file_path = await self._persist_upload(document)
        extracted_text = await self.document_service.extract_text(file_path)
        return await self.process_text(
            user_id=user_id,
            text=extracted_text,
            channel="document",
            source_language=None,
            preferred_output_language=preferred_output_language,
            include_audio=include_audio,
        )

    async def translate_only(
        self,
        *,
        text: str,
        source_language: str | None,
        target_language: str,
    ) -> dict[str, str | float | None]:
        source_lang = self._resolve_source_language(text, source_language)
        target_lang = self.language_service.normalize_code(target_language)
        translation = await self.translator.translate(
            text,
            source_language=source_lang,
            target_language=target_lang,
        )
        return {
            "source_language": source_lang,
            "target_language": target_lang,
            "translated_text": translation.translated_text,
            "confidence": translation.confidence,
        }

    def set_user_language(self, user_id: str, language_code: str) -> None:
        normalized = self.language_service.normalize_code(language_code)
        self.preference_repository.set_preferred_language(user_id, normalized)

    def _resolve_source_language(self, text: str, source_language: str | None) -> str:
        if source_language:
            return self.language_service.normalize_code(source_language)
        return self.language_service.detect(text).language_code

    def _resolve_target_language(self, user_id: str, preferred_output_language: str | None) -> str:
        if preferred_output_language:
            normalized = self.language_service.normalize_code(preferred_output_language)
            self.preference_repository.set_preferred_language(user_id, normalized)
            return normalized

        stored = self.preference_repository.get_preferred_language(user_id)
        if stored:
            return self.language_service.normalize_code(stored)
        return self.language_service.normalize_code(self.default_output_language)

    async def _persist_upload(self, upload: UploadFile) -> Path:
        suffix = Path(upload.filename or "").suffix or ".bin"
        destination = self.temp_upload_dir / f"{uuid4().hex}{suffix}"
        contents = await upload.read()
        if not contents:
            raise PipelineError("Uploaded file is empty", code="empty_upload", status_code=422)
        destination.write_bytes(contents)
        return destination
