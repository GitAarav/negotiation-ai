from __future__ import annotations

import io
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

from app.errors import DocumentProcessingError


class DocumentService:
    def __init__(self, tesseract_cmd: str | None = None) -> None:
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    async def extract_text(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return await self._extract_from_pdf(file_path)
        if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
            return await self._extract_from_image(file_path)
        raise DocumentProcessingError(f"Unsupported document type: {suffix}")

    async def _extract_from_pdf(self, file_path: Path) -> str:
        try:
            with fitz.open(file_path) as document:
                extracted_pages = [page.get_text("text") for page in document]
                text = "\n".join(chunk.strip() for chunk in extracted_pages if chunk.strip()).strip()
                if text:
                    return text

            with fitz.open(file_path) as document:
                ocr_pages: list[str] = []
                for page in document:
                    pixmap = page.get_pixmap(dpi=200)
                    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                    ocr_pages.append(pytesseract.image_to_string(image))
                text = "\n".join(chunk.strip() for chunk in ocr_pages if chunk.strip()).strip()
                if text:
                    return text
        except Exception as exc:
            raise DocumentProcessingError(str(exc)) from exc

        raise DocumentProcessingError("No text could be extracted from the PDF")

    async def _extract_from_image(self, file_path: Path) -> str:
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image).strip()
        except Exception as exc:
            raise DocumentProcessingError(str(exc)) from exc
        if not text:
            raise DocumentProcessingError("No text could be extracted from the image")
        return text
