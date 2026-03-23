from __future__ import annotations

import re


MULTISPACE_RE = re.compile(r"[ \t]+")
MULTIBREAK_RE = re.compile(r"\n{3,}")


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = MULTISPACE_RE.sub(" ", text)

    lines = [line.strip() for line in text.split("\n")]
    collapsed = "\n".join(line for line in lines if line)
    collapsed = MULTIBREAK_RE.sub("\n\n", collapsed)

    return collapsed.strip()

