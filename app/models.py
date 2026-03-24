from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LanguageDetectionResult(BaseModel):
    language_code: str
    confidence: float | None = None


class TranslationResult(BaseModel):
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    confidence: float | None = None


class NegotiationResponse(BaseModel):
    suggestion: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class UserPreferenceUpdate(BaseModel):
    preferred_language: str


class TextProcessRequest(BaseModel):
    user_id: str
    text: str
    source_language: str | None = None
    preferred_output_language: str | None = None
    include_audio: bool = False


class TranslationRequest(BaseModel):
    text: str
    source_language: str | None = None
    target_language: str


class StoredInteraction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    channel: Literal["text", "speech", "document"]
    source_language: str
    target_language: str
    original_text: str
    english_text: str
    negotiation_response_en: str
    localized_response_text: str
    created_at: datetime


class PipelineResponse(BaseModel):
    interaction_id: int
    user_id: str
    channel: Literal["text", "speech", "document"]
    source_language: str
    target_language: str
    original_text: str
    english_input: str
    english_response: str
    localized_response_text: str
    localized_response_audio_base64: str | None = None
    translation_confidence: float | None = None
    side_by_side: dict[str, str] | None = None


class SpeechTranscriptionResponse(BaseModel):
    transcript: str
    detected_language: str
    confidence: float | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
