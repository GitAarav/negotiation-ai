from __future__ import annotations

import mimetypes
from pathlib import Path


TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def detect_file_type(filename: str, supplied_mime_type: str | None = None) -> dict:
    extension = Path(filename or "").suffix.lower()
    guessed_mime = supplied_mime_type or mimetypes.guess_type(filename or "")[0] or "application/octet-stream"

    if extension in TEXT_EXTENSIONS or guessed_mime.startswith("text/"):
        source_type = "text"
    elif extension in DOCUMENT_EXTENSIONS:
        source_type = "document"
    elif extension in IMAGE_EXTENSIONS or guessed_mime.startswith("image/"):
        source_type = "image"
    else:
        source_type = "unknown"

    return {
        "filename": filename or "unknown",
        "extension": extension,
        "mime_type": guessed_mime,
        "source_type": source_type,
    }

