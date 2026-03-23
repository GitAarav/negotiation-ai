from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ExtractedEntities(BaseModel):
    dates: List[str] = Field(default_factory=list)
    amounts: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)


class TextBlock(BaseModel):
    heading: Optional[str] = None
    text: str


class ConfidenceBlock(BaseModel):
    extraction: float = 0.0
    ocr: float = 0.0
    structure: float = 0.0


class ParsingMeta(BaseModel):
    filename: str
    mime_type: str
    extension: str
    source_type: str
    extractor_used: str
    used_ocr: bool = False
    used_llm: bool = False
    warnings: List[str] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    source_type: str
    document_type: str
    title: Optional[str] = None
    raw_text: str
    clean_text: str
    text_blocks: List[TextBlock] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    confidence: ConfidenceBlock = Field(default_factory=ConfidenceBlock)
    meta: ParsingMeta
