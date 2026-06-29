from __future__ import annotations

import re
from pathlib import Path

from .base import Chunk, make_id, split_sections

SKIP_FILES = {"INDEX.md"}


def parse_sources_table(content: str) -> list[dict]:
    refs: list[dict] = []
    match = re.search(r"## Sources\s*\n+(\|[^\n]+\|\n\|[-| :]+\|\n(?:\|[^\n]+\|\n?)+)", content)
    if not match:
        return refs
    lines = [l.strip() for l in match.group(1).splitlines() if l.strip().startswith("|")]
    for line in lines[2:]:
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 2:
            refs.append({"source": cols[0], "location": cols[1], "role": cols[2] if len(cols) > 2 else ""})
    return refs


def chunk_wiki(wiki_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(wiki_dir.glob("*.md")):
        if path.name in SKIP_FILES:
            continue
        content = path.read_text(encoding="utf-8")
        concept = path.stem
        book_refs = parse_sources_table(content)
        body = re.split(r"## Sources", content, maxsplit=1)[0]
        body = re.split(r"## Related Topics", body, maxsplit=1)[0]
        sections = split_sections(body, r"(?m)^(### .+)$")
        for heading, text in sections:
            if not text or len(text) < 30:
                continue
            title = heading.removeprefix("### ").strip() if heading else concept
            chunk_id = f"wiki:{concept}#{slugify(title)}"
            chunks.append(
                Chunk(
                    id=make_id(chunk_id),
                    text=f"{title}\n\n{text}" if heading else text,
                    source="wiki",
                    title=f"wiki/{concept} — {title}",
                    concept=concept,
                    lang="en",
                    priority="high",
                    book_refs=book_refs,
                )
            )
    return chunks


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60] or "section"
