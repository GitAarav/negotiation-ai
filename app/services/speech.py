from pathlib import Path

import whisper

from app.errors import SpeechProcessingError
from app.models import SpeechTranscriptionResponse


class SpeechToTextService:
    def __init__(self, model_size: str, device: str = "cpu") -> None:
        self.model_size = model_size
        self.device = device
        self.model = None

    async def transcribe(self, file_path: Path) -> SpeechTranscriptionResponse:
        try:
            if self.model is None:
                self.model = whisper.load_model(self.model_size, device=self.device)
            result = self.model.transcribe(str(file_path))
        except Exception as exc:
            raise SpeechProcessingError(str(exc)) from exc

        transcript = result.get("text", "").strip()
        detected_language = result.get("language", "unknown")
        if not transcript:
            raise SpeechProcessingError("No speech could be transcribed from the audio file")

        return SpeechTranscriptionResponse(
            transcript=transcript,
            detected_language=detected_language,
            confidence=None,
        )
