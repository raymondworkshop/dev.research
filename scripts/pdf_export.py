#!/usr/bin/env python3
"""Export PDF file highlights to notes/ as Markdown (books-export twin).

Reads annotation objects embedded in books/*.pdf (Preview, Adobe, Books
“export annotations into file”, etc.).

Color labels (same as books-export):
  green → important chapter/theme heading (###)
  purple → **bold**
  yellow → [info]
  pink → [insights]
  blue → [how]

Usage:
  make pdf-export LIST=1
  make pdf-export BOOK='Seduction Bible'
"""
from __future__ import annotations

import argparse
import colorsys
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "notes"
BOOKS_DIR = ROOT / "books"

# Mirror Apple Books ZANNOTATIONSTYLE buckets
STYLE_BUCKET = {
    1: "important",  # green → ###
    2: "how",  # blue
    3: "info",  # yellow
    4: "insights",  # pink
    5: "insights",  # purple (rendered as **bold**)
}

# Reference RGB (0–1) matching common Books / Preview highlight swatches
REF_COLORS: list[tuple[int, tuple[float, float, float]]] = [
    (1, (0.486, 0.784, 0.408)),  # green
    (2, (0.412, 0.690, 0.945)),  # blue
    (3, (0.980, 0.804, 0.353)),  # yellow
    (4, (0.984, 0.361, 0.537)),  # pink
    (5, (0.784, 0.522, 0.855)),  # purple
]

# Markup annotation subtypes in PyMuPDF: Highlight, Underline, Squiggly, StrikeOut
MARKUP_TYPES = {8, 9, 10, 11}


@dataclass
class Highlight:
    text: str
    note: str | None
    style: int | None
    page: int  # 1-based
    y0: float
    x0: float
    rect: tuple[float, float, float, float]


@dataclass
class BookExport:
    title: str
    author: str
    source_path: Path
    highlights: list[Highlight]


def slugify(text: str, max_len: int = 80) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]+", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return (text or "untitled")[:max_len].rstrip("-")


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text.lower())


def title_key(text: str) -> str:
    key = normalize(text)
    return key[3:] if key.startswith("the") and len(key) > 3 else key


def bucket_for(style: int | None) -> str:
    if style is None:
        return "other"
    return STYLE_BUCKET.get(style, "other")


def _rgb_distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def style_from_rgb(rgb: list[float] | tuple[float, ...] | None) -> int:
    """Map annot stroke RGB to books-export style int."""
    if not rgb or len(rgb) < 3:
        return 3  # default yellow/info
    r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
    # Prefer nearest known Books swatch when close enough
    best_style, best_dist = 3, 10.0
    for style, ref in REF_COLORS:
        dist = _rgb_distance((r, g, b), ref)
        if dist < best_dist:
            best_style, best_dist = style, dist
    if best_dist < 0.08:
        return best_style

    # Fallback: HSV hue buckets
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.15 or v < 0.2:
        return 3
    deg = h * 360
    if 70 <= deg < 160:
        return 1  # green
    if 160 <= deg < 255:
        return 2  # blue
    if 255 <= deg < 295:
        return 5  # purple
    if 295 <= deg or deg < 20:
        return 4  # pink / magenta / red-pink
    if 20 <= deg < 70:
        return 3  # yellow / orange
    return 3


def extract_markup_text(page, annot) -> str:
    """Recover selected text under a markup annotation via word centers."""
    import pymupdf

    vertices = annot.vertices
    if not vertices or len(vertices) < 4:
        return _norm_space(page.get_textbox(annot.rect + (-2, -2, 2, 2)))

    quads = [
        pymupdf.Quad(vertices[i : i + 4]) for i in range(0, len(vertices), 4)
    ]
    # Expand slightly — Preview/Canva quads often clip glyph boxes tightly
    pads = [q.rect + (-1.5, -1.5, 1.5, 1.5) for q in quads]
    words = page.get_text("words")
    hits: list[tuple] = []
    for word in words:
        wr = pymupdf.Rect(word[:4])
        area = max(wr.get_area(), 1e-6)
        center = pymupdf.Point((wr.x0 + wr.x1) / 2, (wr.y0 + wr.y1) / 2)
        for qr in pads:
            if qr.contains(center):
                hits.append(word)
                break
            inter = wr & qr
            if inter.is_empty:
                continue
            if inter.get_area() / area >= 0.25:
                hits.append(word)
                break

    hits.sort(key=lambda w: (w[5], w[6], w[7]))
    seen: set[tuple[int, int, int]] = set()
    parts: list[str] = []
    for word in hits:
        key = (int(word[5]), int(word[6]), int(word[7]))
        if key in seen:
            continue
        seen.add(key)
        parts.append(str(word[4]))
    text = _norm_space(" ".join(parts))
    if text:
        return text
    # Fallback for odd layouts
    chunks = [_norm_space(page.get_textbox(qr)) for qr in pads]
    return _norm_space(" ".join(c for c in chunks if c))


def _norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _overlap_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if shorter in longer:
        return 1.0
    sa, sb = set(a.lower().split()), set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _join_highlight_text(a: str, b: str) -> str:
    if not a:
        return b
    if not b:
        return a
    if a in b:
        return b
    if b in a:
        return a
    # Prefer longer when they share most tokens (fragmented re-highlights)
    if _overlap_ratio(a, b) >= 0.55:
        return a if len(a) >= len(b) else b
    return _norm_space(f"{a} {b}")


def merge_overlapping(highlights: list[Highlight]) -> list[Highlight]:
    """Collapse near-duplicate / adjacent same-color selections on a page."""
    if not highlights:
        return []
    ordered = sorted(highlights, key=lambda h: (h.page, h.style or 0, h.y0, h.x0))
    merged: list[Highlight] = []
    for h in ordered:
        if not merged:
            merged.append(h)
            continue
        prev = merged[-1]
        if prev.page != h.page or prev.style != h.style:
            merged.append(h)
            continue
        px0, py0, px1, py1 = prev.rect
        hx0, hy0, hx1, hy1 = h.rect
        gap = hy0 - py1
        vertically_close = gap < 22 and gap > -max(py1 - py0, hy1 - hy0)
        overlaps = _overlap_ratio(prev.text, h.text) >= 0.3
        # Same-color line wraps from Preview often become separate annots
        adjacent_lines = vertically_close and (overlaps or gap < 14)
        if adjacent_lines or overlaps:
            text = _join_highlight_text(prev.text, h.text)
            note_parts = [n for n in (prev.note, h.note) if n]
            note = " | ".join(dict.fromkeys(note_parts)) or None
            rect = (min(px0, hx0), min(py0, hy0), max(px1, hx1), max(py1, hy1))
            merged[-1] = Highlight(
                text=text,
                note=note,
                style=prev.style,
                page=prev.page,
                y0=rect[1],
                x0=rect[0],
                rect=rect,
            )
            continue
        merged.append(h)
    return merged


def load_pdf_highlights(path: Path) -> BookExport:
    try:
        import pymupdf
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pymupdf is required. Install via the project venv "
            "(make pdf-export sets this up)."
        ) from exc

    doc = pymupdf.open(path)
    try:
        meta = doc.metadata or {}
        # Prefer filename — PDF metadata titles are often wrong (Canva, etc.)
        title = path.stem.strip() or (meta.get("title") or "Untitled").strip()
        author_meta = (meta.get("author") or "").strip()
        # Ignore tiny/placeholder authors like "gg"
        author = author_meta if len(author_meta) >= 3 else "Unknown"

        raw: list[Highlight] = []
        for page in doc:
            for annot in page.annots() or []:
                if annot.type[0] not in MARKUP_TYPES:
                    continue
                text = extract_markup_text(page, annot)
                if not text:
                    continue
                colors = annot.colors or {}
                stroke = colors.get("stroke") or colors.get("fill")
                style = style_from_rgb(stroke)
                note = (annot.info or {}).get("content") or None
                if note:
                    note = note.strip() or None
                rect = annot.rect
                raw.append(
                    Highlight(
                        text=text,
                        note=note,
                        style=style,
                        page=page.number + 1,
                        y0=float(rect.y0),
                        x0=float(rect.x0),
                        rect=(
                            float(rect.x0),
                            float(rect.y0),
                            float(rect.x1),
                            float(rect.y1),
                        ),
                    )
                )
    finally:
        doc.close()

    return BookExport(
        title=title,
        author=author,
        source_path=path,
        highlights=merge_overlapping(raw),
    )


def pdf_books() -> list[Path]:
    if not BOOKS_DIR.is_dir():
        return []
    return sorted(
        path
        for path in BOOKS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() == ".pdf"
    )


def find_pdfs(query: str | None) -> list[Path]:
    candidates = pdf_books()
    if not candidates:
        raise ValueError(f"No PDF files found in {BOOKS_DIR}")
    if not query:
        return candidates

    q = normalize(query)
    exact = [
        path
        for path in candidates
        if q in {normalize(path.name), normalize(path.stem)}
    ]
    if len(exact) == 1:
        return exact
    if len(exact) > 1:
        raise ValueError(
            "Multiple PDFs matched exactly: " + ", ".join(p.name for p in exact)
        )

    partial = [path for path in candidates if q and q in normalize(path.name)]
    if len(partial) == 1:
        return partial
    if len(partial) > 1:
        raise ValueError(
            "Multiple PDFs matched: " + ", ".join(p.name for p in partial)
        )
    raise ValueError(
        f"No PDF matched {query!r}. Available: "
        + ", ".join(p.name for p in candidates)
    )


def render_highlight(h: Highlight) -> list[str]:
    if h.style == 1:
        return [f"### {h.text}", ""]
    if h.style == 5:
        lines = [f"- **{h.text}**"]
    else:
        label = bucket_for(h.style)
        lines = [f"- [{label}] {h.text}"]
    if h.note:
        lines.append(f"  - note: {h.note}")
    return lines


def group_by_page(book: BookExport) -> list[tuple[str, list[Highlight]]]:
    by_page: dict[int, list[Highlight]] = defaultdict(list)
    for h in book.highlights:
        by_page[h.page].append(h)
    groups: list[tuple[str, list[Highlight]]] = []
    for page in sorted(by_page):
        items = sorted(by_page[page], key=lambda h: (h.y0, h.x0, h.text))
        groups.append((f"Page {page}", items))
    return groups


def render_markdown(book: BookExport) -> str:
    groups = group_by_page(book)
    rel = book.source_path.relative_to(ROOT) if book.source_path.is_relative_to(ROOT) else book.source_path
    lines = [
        "---",
        f'title: "{book.title.replace(chr(34), chr(39))}"',
        f'author: "{book.author.replace(chr(34), chr(39))}"',
        f"source_file: {rel}",
        f"highlights: {len(book.highlights)}",
        f"exported: {datetime.now(tz=timezone.utc).date().isoformat()}",
        "source: pdf-annotations",
        "labels: green→theme heading; purple→bold; yellow→info; pink→insights; blue→how",
        "---",
        "",
        f"# {book.title}",
        "",
        f"*{book.author}*",
        "",
        "> Grouped by page. Green → ### theme; purple → **bold**; pink → [insights]; blue → [how]; yellow → [info].",
        "",
    ]
    for topic, items in groups:
        if not items:
            continue
        lines.append(f"## {topic}")
        lines.append("")
        for h in items:
            if h.style == 1 and title_key(h.text) == title_key(topic):
                continue
            rendered = render_highlight(h)
            lines.extend(rendered)
            if h.style != 1:
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_export(book: BookExport, out_dir: Path) -> Path | None:
    if not book.highlights:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=timezone.utc).date().isoformat()
    path = out_dir / f"{today}-{slugify(book.title)}.md"
    path.write_text(render_markdown(book), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export PDF highlight annotations from books/ to notes/."
    )
    parser.add_argument(
        "book",
        nargs="?",
        help='PDF name match in books/ (example: "Seduction Bible")',
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List PDFs with highlight counts; do not write files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=OUT_DIR,
        help=f"Output directory (default: {OUT_DIR})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        paths = find_pdfs(args.book)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    exports: list[BookExport] = []
    try:
        for path in paths:
            exports.append(load_pdf_highlights(path))
    except ModuleNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — surface PDF parse errors cleanly
        print(f"ERROR: failed reading PDF: {exc}", file=sys.stderr)
        return 1

    # Only show / write books that have highlights unless listing a specific match
    with_hl = [book for book in exports if book.highlights]
    if args.book and not with_hl and exports:
        # User asked for a specific PDF that has zero annotations
        book = exports[0]
        print(
            f"No highlight annotations in {book.source_path.name}",
            file=sys.stderr,
        )
        return 1
    if not args.book:
        exports = with_hl

    if args.list:
        total = sum(len(book.highlights) for book in exports)
        print(f"{len(exports)} PDFs, {total} highlights\n")
        for book in sorted(exports, key=lambda b: b.title.lower()):
            print(
                f"{len(book.highlights):5}  {book.source_path.name} — {book.author}"
            )
        return 0

    if not exports:
        print("No PDFs with highlight annotations found in books/.")
        return 1

    written: list[Path] = []
    skipped = 0
    for book in exports:
        path = write_export(book, args.output)
        if path is None:
            skipped += 1
            continue
        written.append(path)

    total = sum(len(book.highlights) for book in exports if book.highlights)
    print(f"Wrote {len(written)} file(s), {total} highlights → {args.output}")
    for path in written:
        try:
            print(f"  {path.relative_to(ROOT)}")
        except ValueError:
            print(f"  {path}")
    if skipped:
        print(f"Skipped {skipped} PDF(s) with 0 highlights.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
