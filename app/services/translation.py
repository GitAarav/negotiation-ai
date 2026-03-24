from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncOpenAI

from app.errors import TranslationFailure
from app.models import TranslationResult


class Translator(ABC):
    @abstractmethod
    async def translate(
        self,
        text: str,
        *,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        raise NotImplementedError


class OpenAITranslator(Translator):
    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def translate(
        self,
        text: str,
        *,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        prompt = (
            "Translate the user text while preserving intent, tone, legal nuance, and formatting. "
            "Return only the translated text."
        )
        try:
            response = await self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Source language: {source_language}\n"
                            f"Target language: {target_language}\n"
                            f"Text:\n{text}"
                        ),
                    },
                ],
            )
        except Exception as exc:
            raise TranslationFailure(str(exc)) from exc

        translated = response.output_text.strip()
        if not translated:
            raise TranslationFailure("Translator returned empty text")

        return TranslationResult(
            source_language=source_language,
            target_language=target_language,
            original_text=text,
            translated_text=translated,
            confidence=None,
        )


class StubTranslator(Translator):
    async def translate(
        self,
        text: str,
        *,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        raise TranslationFailure(
            "Translation provider is not configured. Set OPENAI_API_KEY to enable translations."
        )


def build_translator(provider: str, **kwargs: Any) -> Translator:
    if provider == "openai" and kwargs.get("api_key"):
        return OpenAITranslator(kwargs["api_key"], kwargs["model"])
    return StubTranslator()
