from __future__ import annotations

import io


def extract_text_from_image(content: bytes) -> tuple[str, str, list[str], float]:
    warnings: list[str] = []

    try:
        from PIL import Image, ImageOps
    except ImportError:
        warnings.append("Pillow is not installed.")
        return "", "image_unavailable", warnings, 0.0

    try:
        import pytesseract
    except ImportError:
        warnings.append("pytesseract is not installed.")
        return "", "ocr_unavailable", warnings, 0.0

    image = Image.open(io.BytesIO(content))
    grayscale = ImageOps.grayscale(image)
    text = pytesseract.image_to_string(grayscale)

    confidence = 0.75 if text.strip() else 0.0
    if not text.strip():
        warnings.append("OCR ran but returned very little text.")

    return text, "pytesseract", warnings, confidence


def extract_text_from_pdf_ocr(content: bytes) -> tuple[str, str, list[str], float]:
    warnings: list[str] = []

    try:
        import pypdfium2 as pdfium
    except ImportError:
        warnings.append("pypdfium2 is not installed.")
        return "", "pdf_ocr_unavailable", warnings, 0.0

    try:
        import pytesseract
    except ImportError:
        warnings.append("pytesseract is not installed.")
        return "", "pdf_ocr_unavailable", warnings, 0.0

    document = pdfium.PdfDocument(io.BytesIO(content))
    page_text: list[str] = []

    for index in range(len(document)):
        page = document[index]
        bitmap = page.render(scale=2)
        image = bitmap.to_pil()
        page_text.append(pytesseract.image_to_string(image))

    text = "\n".join(part for part in page_text if part).strip()
    confidence = 0.7 if text else 0.0
    if not text:
        warnings.append("PDF OCR ran but returned very little text.")

    return text, "pdfium_pytesseract", warnings, confidence
