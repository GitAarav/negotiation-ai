from __future__ import annotations

from app.schemas.parser import ParsedDocument, ParsingMeta
from app.services.file_classifier import detect_file_type
from app.services.normalizer import normalize_text
from app.services.structurer import build_rule_based_structure
from app.services.text_extractors.document_text import (
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_from_plain_text,
)
from app.services.text_extractors.image_ocr import extract_text_from_image, extract_text_from_pdf_ocr


def parse_document(filename: str, content: bytes, mime_type: str | None = None) -> dict:
    file_info = detect_file_type(filename, mime_type)
    raw_text, extractor_used, warnings, used_ocr, ocr_confidence = _extract_raw_text(file_info, content)

    clean_text = normalize_text(raw_text)
    structured = build_rule_based_structure(clean_text, file_info["source_type"])

    payload = {
        "source_type": file_info["source_type"],
        "document_type": structured["document_type"],
        "title": structured["title"],
        "raw_text": raw_text,
        "clean_text": clean_text,
        "text_blocks": [_dump_model(block) for block in structured["text_blocks"]],
        "highlights": structured["highlights"],
        "entities": _dump_model(structured["entities"]),
        "confidence": _dump_model(structured["confidence"]),
        "meta": _dump_model(
            ParsingMeta(
                filename=file_info["filename"],
                mime_type=file_info["mime_type"],
                extension=file_info["extension"],
                source_type=file_info["source_type"],
                extractor_used=extractor_used,
                used_ocr=used_ocr,
                used_llm=False,
                warnings=warnings,
            )
        ),
    }

    payload["confidence"]["ocr"] = ocr_confidence
    validated = _validate_model(ParsedDocument, payload)
    return _dump_model(validated)


def _extract_raw_text(file_info: dict, content: bytes) -> tuple[str, str, list[str], bool, float]:
    extension = file_info["extension"]
    source_type = file_info["source_type"]

    if source_type == "text":
        text, extractor, warnings = extract_text_from_plain_text(content)
        return text, extractor, warnings, False, 0.0

    if extension == ".pdf":
        text, extractor, warnings = extract_text_from_pdf(content)
        if text.strip():
            return text, extractor, warnings, False, 0.0

        ocr_text, ocr_extractor, ocr_warnings, ocr_confidence = extract_text_from_pdf_ocr(content)
        return ocr_text, ocr_extractor, warnings + ocr_warnings, True, ocr_confidence

    if extension == ".docx":
        text, extractor, warnings = extract_text_from_docx(content)
        return text, extractor, warnings, False, 0.0

    if source_type == "image":
        text, extractor, warnings, confidence = extract_text_from_image(content)
        return text, extractor, warnings, True, confidence

    text, extractor, warnings = extract_text_from_plain_text(content)
    warnings.append("Unknown file type; attempted plain text parsing.")
    return text, extractor, warnings, False, 0.0


def _dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _validate_model(model_class, payload: dict):
    if hasattr(model_class, "model_validate"):
        return model_class.model_validate(payload)
    return model_class.parse_obj(payload)
