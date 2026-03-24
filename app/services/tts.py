import base64

import httpx

from app.errors import PipelineError


class TextToSpeechService:
    def __init__(self, api_key: str | None, voice_id: str | None, model_id: str) -> None:
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id

    async def synthesize(self, text: str, language_code: str) -> str | None:
        if not self.api_key or not self.voice_id:
            return None

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.75,
            },
            "language_code": language_code,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except Exception as exc:
            raise PipelineError(
                f"Text-to-speech generation failed: {exc}",
                code="tts_failed",
                status_code=502,
            ) from exc

        return base64.b64encode(response.content).decode("utf-8")
