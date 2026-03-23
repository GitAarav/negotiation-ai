from __future__ import annotations

import re

from app.schemas.parser import ConfidenceBlock, ExtractedEntities, TextBlock


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4})")
URL_RE = re.compile(r"\bhttps?://[^\s]+")
AMOUNT_RE = re.compile(r"(?:₹|Rs\.?|INR|\$|USD|EUR)\s?\d[\d,]*(?:\.\d+)?")
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b",
    re.IGNORECASE,
)


def build_rule_based_structure(clean_text: str, source_type: str) -> dict:
    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    entities = ExtractedEntities(
        dates=_dedupe(DATE_RE.findall(clean_text)),
        amounts=_dedupe(AMOUNT_RE.findall(clean_text)),
        phones=_dedupe(_filter_phone_matches(PHONE_RE.findall(clean_text))),
        emails=_dedupe(EMAIL_RE.findall(clean_text)),
        urls=_dedupe(URL_RE.findall(clean_text)),
    )

    text_blocks = _build_text_blocks(lines)
    highlights = lines[:12]
    confidence = ConfidenceBlock(
        extraction=_estimate_extraction_confidence(clean_text),
        ocr=0.0,
        structure=_estimate_structure_confidence(lines, entities, source_type),
    )

    return {
        "document_type": _guess_document_type(clean_text, source_type),
        "title": lines[0][:140] if lines else None,
        "text_blocks": text_blocks,
        "highlights": highlights,
        "entities": entities,
        "confidence": confidence,
    }


def _build_text_blocks(lines: list[str]) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    buffer: list[str] = []
    current_heading: str | None = None

    for line in lines:
        if _looks_like_heading(line):
            if buffer:
                blocks.append(TextBlock(heading=current_heading, text="\n".join(buffer)))
                buffer = []
            current_heading = line
            continue

        buffer.append(line)

        if len(buffer) >= 8:
            blocks.append(TextBlock(heading=current_heading, text="\n".join(buffer)))
            buffer = []
            current_heading = None

    if buffer:
        blocks.append(TextBlock(heading=current_heading, text="\n".join(buffer)))

    return blocks[:20]


def _looks_like_heading(line: str) -> bool:
    if len(line) > 80 or len(line) < 3:
        return False
    if line.isupper():
        return True
    lowered = line.lower()
    return lowered.endswith(":") or lowered in {
        "education",
        "experience",
        "skills",
        "summary",
        "projects",
        "employment",
        "work experience",
        "professional summary",
    }


def _guess_document_type(clean_text: str, source_type: str) -> str:
    lowered = clean_text.lower()
    if "resume" in lowered or "curriculum vitae" in lowered or "professional summary" in lowered:
        return "resume"
    if "invoice" in lowered or "amount due" in lowered:
        return "invoice"
    if "agreement" in lowered or "contract" in lowered:
        return "agreement"
    if "notice" in lowered:
        return "notice"
    if "petitioner" in lowered or "respondent" in lowered or "court" in lowered:
        return "legal_document"
    if source_type == "image":
        return "image_text"
    if source_type == "document":
        return "document"
    return "text"


def _estimate_extraction_confidence(clean_text: str) -> float:
    if not clean_text:
        return 0.0
    if len(clean_text) > 1200:
        return 0.9
    if len(clean_text) > 400:
        return 0.8
    if len(clean_text) > 120:
        return 0.65
    return 0.4


def _estimate_structure_confidence(lines: list[str], entities: ExtractedEntities, source_type: str) -> float:
    score = 0.25
    if lines:
        score += 0.25
    if any([entities.dates, entities.amounts, entities.phones, entities.emails, entities.urls]):
        score += 0.2
    if source_type in {"text", "document"}:
        score += 0.1
    if len(lines) > 10:
        score += 0.1
    return min(score, 0.9)


def _filter_phone_matches(matches: list[str]) -> list[str]:
    filtered: list[str] = []
    for match in matches:
        digits = re.sub(r"\D", "", match)
        if 7 <= len(digits) <= 15:
            filtered.append(match.strip())
    return filtered


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
