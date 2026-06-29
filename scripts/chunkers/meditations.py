from __future__ import annotations

import re
from pathlib import Path

from .base import Chunk, make_id, slugify

VOLUME_RE = re.compile(r"^# (卷 [一二三四五六七八九十]+|\u5377 \d+)", re.MULTILINE)


def chunk_meditations(path: Path) -> list[Chunk]:
    content = path.read_text(encoding="utf-8")
    toc_end = content.find("# 卷")
    if toc_end == -1:
        return []
    content = content[toc_end:]
    chunks: list[Chunk] = []
    matches = list(VOLUME_RE.finditer(content))
    for i, match in enumerate(matches):
        volume = match.group(1).strip()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[match.end() : end].strip()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if len(p.strip()) > 40]
        if not paragraphs:
            continue
        group: list[str] = []
        group_len = 0
        part = 0
        for para in paragraphs:
            group.append(para)
            group_len += len(para)
            if group_len >= 500:
                part += 1
                text = "\n\n".join(group)
                slug = slugify(f"{volume}-part-{part}")
                chunk_id = f"meditations:{slug}"
                chunks.append(
                    Chunk(
                        id=make_id(chunk_id),
                        text=f"{volume}\n\n{text[:2500]}",
                        source="meditations",
                        title=f"meditations/{volume}" + (f" (part {part})" if part > 1 else ""),
                        concept=volume,
                        lang="zh",
                        priority="high",
                    )
                )
                group = []
                group_len = 0
        if group:
            part += 1
            text = "\n\n".join(group)
            slug = slugify(f"{volume}-part-{part}")
            chunk_id = f"meditations:{slug}"
            chunks.append(
                Chunk(
                    id=make_id(chunk_id),
                    text=f"{volume}\n\n{text[:2500]}",
                    source="meditations",
                    title=f"meditations/{volume}" + (f" (part {part})" if part > 1 else ""),
                    concept=volume,
                    lang="zh",
                    priority="high",
                )
            )
    return chunks
