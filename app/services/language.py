import re

from langdetect import DetectorFactory, LangDetectException, detect_langs

from app.errors import UnsupportedLanguageError
from app.models import LanguageDetectionResult

DetectorFactory.seed = 0


class LanguageService:
    def __init__(self, supported_languages: list[str]) -> None:
        self.supported_languages = set(code.lower() for code in supported_languages)
        self.language_pattern = re.compile(r"^[a-z]{2,3}(-[a-z]{2,4})?$")

    def normalize_code(self, language_code: str) -> str:
        normalized = language_code.lower()
        alias_map = {
            "zh": "zh-cn",
            "zh-hans": "zh-cn",
            "zh-hant": "zh-tw",
            "pt-br": "pt",
        }
        normalized = alias_map.get(normalized, normalized)
        if normalized in self.supported_languages:
            return normalized
        if not self.language_pattern.match(normalized):
            raise UnsupportedLanguageError(normalized)
        return normalized

    def detect(self, text: str) -> LanguageDetectionResult:
        try:
            results = detect_langs(text)
        except LangDetectException as exc:
            raise UnsupportedLanguageError("unknown") from exc
        top = results[0]
        normalized = self.normalize_code(top.lang)
        return LanguageDetectionResult(language_code=normalized, confidence=float(top.prob))
