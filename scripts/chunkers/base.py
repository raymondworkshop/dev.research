from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    title: str
    concept: str = ""
    emotions: list[str] = field(default_factory=list)
    lang: str = "en"
    priority: str = "medium"
    book_refs: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "title": self.title,
            "concept": self.concept,
            "emotions": self.emotions,
            "lang": self.lang,
            "priority": self.priority,
            "book_refs": self.book_refs,
        }


def make_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80] or "section"


def clean_epub_spacing(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if re.match(r"^[A-Z]( [A-Z])+[,.]?", line.strip()):
            line = line.replace(" ", "")
        lines.append(line)
    return "\n".join(lines)


def split_sections(content: str, pattern: str) -> list[tuple[str, str]]:
    parts = re.split(pattern, content, flags=re.MULTILINE)
    if len(parts) < 2:
        return [("", content.strip())] if content.strip() else []
    sections: list[tuple[str, str]] = []
    if parts[0].strip():
        sections.append(("", parts[0].strip()))
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            sections.append((heading, body))
    return sections
