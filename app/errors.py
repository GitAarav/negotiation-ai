class PipelineError(Exception):
    """Base error for recoverable pipeline failures."""

    def __init__(self, message: str, *, code: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class UnsupportedLanguageError(PipelineError):
    def __init__(self, language_code: str) -> None:
        super().__init__(
            f"Unsupported language code: {language_code}",
            code="unsupported_language",
            status_code=422,
        )


class TranslationFailure(PipelineError):
    def __init__(self, message: str = "Translation failed") -> None:
        super().__init__(message, code="translation_failed", status_code=502)


class ExternalAPIFailure(PipelineError):
    def __init__(self, message: str = "Negotiation API request failed") -> None:
        super().__init__(message, code="negotiation_api_failed", status_code=502)


class DocumentProcessingError(PipelineError):
    def __init__(self, message: str = "Document processing failed") -> None:
        super().__init__(message, code="document_processing_failed", status_code=422)


class SpeechProcessingError(PipelineError):
    def __init__(self, message: str = "Speech processing failed") -> None:
        super().__init__(message, code="speech_processing_failed", status_code=422)
