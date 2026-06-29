from __future__ import annotations

import re
from pathlib import Path

from .base import Chunk, clean_epub_spacing, make_id, slugify

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
MEDITATION_RE = re.compile(rf"^### ({MONTHS}) (\d+)(?:st|nd|rd|th)?\s*\*\*(.+?)\*\*", re.MULTILINE)


def chunk_daily_stoic(path: Path) -> list[Chunk]:
    content = path.read_text(encoding="utf-8")
    start = content.find("### January")
    if start == -1:
        return []
    content = content[start:]
    chunks: list[Chunk] = []
    matches = list(MEDITATION_RE.finditer(content))
    for i, match in enumerate(matches):
        month, day, theme = match.group(1), match.group(2), match.group(3).strip()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = clean_epub_spacing(content[match.end() : end].strip())
        if len(body) < 50:
            continue
        title = f"{month} {day} — {theme}"
        slug = slugify(f"{month}-{day}-{theme}")
        chunk_id = f"daily_stoic:{slug}"
        chunks.append(
            Chunk(
                id=make_id(chunk_id),
                text=f"{title}\n\n{body[:2500]}",
                source="daily_stoic",
                title=title,
                concept=theme.lower(),
                lang="en",
                priority="high",
            )
        )
    return chunks
