from __future__ import annotations

import re
from pathlib import Path

from .base import Chunk, make_id, slugify, split_sections

RAW_CONFIG: dict[str, dict] = {
    "2026-04-07-notes-on-stoicism.md": {"pattern": r"(?m)^(#{4,5} .+)$", "topic": "stoicism", "lang": "zh"},
    "2025-02-09-understanding-your-emotions.md": {"pattern": r"(?m)^(#{4,5} .+)$", "topic": "emotions", "lang": "en"},
    "2020-05-19-courage-and-love.md": {"pattern": r"(?m)^(#{3,4} .+)$", "topic": "adler", "lang": "zh-Hans"},
    "2026-03-01-a-free-man.md": {"pattern": r"(?m)^(#{3,4} .+)$", "topic": "career", "lang": "zh-Hant"},
}

SKIP_HEADINGS = {"reference", "references", "notes from"}


def chunk_raw(raw_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for filename, cfg in RAW_CONFIG.items():
        path = raw_dir / filename
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        if content.startswith("---"):
            content = re.sub(r"^---\n.*?\n---\n", "", content, count=1, flags=re.DOTALL)
        sections = split_sections(content, cfg["pattern"])
        seen: dict[str, int] = {}
        for heading, text in sections:
            if not text or len(text) < 40:
                continue
            title_text = heading.lstrip("#").strip() if heading else filename
            if any(skip in title_text.lower() for skip in SKIP_HEADINGS):
                continue
            if not heading and len(text) < 100:
                continue
            level = heading.count("#") if heading else 0
            key = f"{level}:{title_text}"
            seen[key] = seen.get(key, 0) + 1
            occ = seen[key]
            chunk_id = f"raw_summary:{path.stem}#{level}:{title_text}:{occ}"
            chunks.append(
                Chunk(
                    id=make_id(chunk_id),
                    text=f"{title_text}\n\n{text[:2000]}",
                    source="raw_summary",
                    title=f"raw/{path.stem} § {title_text}",
                    concept=cfg["topic"],
                    lang=cfg["lang"],
                    priority="low",
                )
            )
    return chunks
