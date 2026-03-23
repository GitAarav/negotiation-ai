from __future__ import annotations

import io


def extract_text_from_plain_text(content: bytes) -> tuple[str, str, list[str]]:
    warnings: list[str] = []
    try:
        return content.decode("utf-8"), "plain_text", warnings
    except UnicodeDecodeError:
        warnings.append("utf-8 decode failed; used latin-1 fallback.")
        return content.decode("latin-1", errors="ignore"), "plain_text_fallback", warnings


def extract_text_from_pdf(content: bytes) -> tuple[str, str, list[str]]:
    warnings: list[str] = []

    try:
        import pdfplumber
    except ImportError:
        warnings.append("pdfplumber is not installed.")
        return "", "pdf_unavailable", warnings

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    text = "\n".join(page for page in pages if page).strip()
    if not text:
        warnings.append("PDF had little or no embedded text; OCR fallback may be required.")
    return text, "pdfplumber", warnings


def extract_text_from_docx(content: bytes) -> tuple[str, str, list[str]]:
    warnings: list[str] = []

    try:
        from docx import Document
    except ImportError:
        warnings.append("python-docx is not installed.")
        return "", "docx_unavailable", warnings

    document = Document(io.BytesIO(content))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs), "python_docx", warnings

