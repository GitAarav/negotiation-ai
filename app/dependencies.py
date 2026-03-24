from functools import lru_cache

from app.config import get_settings
from app.database import Database
from app.repositories import InteractionRepository, UserPreferenceRepository
from app.services.documents import DocumentService
from app.services.language import LanguageService
from app.services.negotiation import NegotiationClient
from app.services.pipeline import PipelineService
from app.services.speech import SpeechToTextService
from app.services.translation import build_translator
from app.services.tts import TextToSpeechService


@lru_cache
def get_pipeline_service() -> PipelineService:
    settings = get_settings()
    database = Database(settings.storage_path)
    language_service = LanguageService(settings.supported_languages)
    translator = build_translator(
        settings.translator_provider,
        api_key=settings.openai_api_key,
        model=settings.openai_translation_model,
    )

    return PipelineService(
        temp_upload_dir=settings.temp_upload_dir,
        language_service=language_service,
        translator=translator,
        negotiation_client=NegotiationClient(
            settings.negotiation_api_url,
            settings.negotiation_timeout_seconds,
        ),
        tts_service=TextToSpeechService(
            settings.elevenlabs_api_key,
            settings.elevenlabs_voice_id,
            settings.elevenlabs_model_id,
        ),
        speech_service=SpeechToTextService(
            settings.whisper_model_size,
            settings.whisper_device,
        ),
        document_service=DocumentService(settings.tesseract_cmd),
        interaction_repository=InteractionRepository(database),
        preference_repository=UserPreferenceRepository(database),
        enable_side_by_side_text=settings.enable_side_by_side_text,
        default_output_language=settings.default_output_language,
    )
