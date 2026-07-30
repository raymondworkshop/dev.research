#!/usr/bin/env python3
"""Export Apple Books highlights to notes/ as Markdown.

Groups by book topics/chapters (from EPUB when available).
Color labels:
  green → important chapter/theme heading (###)
  purple → **bold**
  yellow → [info]
  pink → [insights]
  blue → [how]

Reads local Books SQLite DBs on macOS.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "notes"
BOOKS_DIR = ROOT / "books"

BOOKS_HOME = Path.home() / "Library/Containers/com.apple.iBooksX/Data/Documents"
ANNOTATION_DIR = BOOKS_HOME / "AEAnnotation"
LIBRARY_DIR = BOOKS_HOME / "BKLibrary"

# Apple Books ZANNOTATIONSTYLE → label
STYLE_BUCKET = {
    1: "important",  # green → ## / ### chapter or theme heading
    2: "how",  # blue
    3: "info",  # yellow
    4: "insights",  # pink
    5: "insights",  # purple (rendered as **bold**)
}

CFI_SPINE_RE = re.compile(r"epubcfi\(/6/(\d+)(?:\[([^\]]+)\])?")
CFI_PATH_RE = re.compile(r"!/4/(\d+)")
SKIP_HTML_TAGS = {
    "script",
    "style",
    "meta",
    "link",
    "br",
    "img",
    "hr",
    "source",
    "area",
    "base",
    "embed",
    "input",
    "param",
    "track",
    "wbr",
}


@dataclass
class Highlight:
    text: str
    note: str | None
    style: int | None
    created: float | None
    modified: float | None
    location: str | None
    range_start: int | None


@dataclass
class BookExport:
    asset_id: str
    title: str
    author: str
    path: str | None
    highlights: list[Highlight]


@dataclass
class TopicInfo:
    key: str
    title: str
    order: tuple[int, int]  # (spine_n, path_even)


class _BodyChildrenParser(HTMLParser):
    """Collect direct children of <body> with EPUB CFI even indices (/4/N)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.depth = 0
        self.even = 0
        self.kids: list[dict[str, str | int]] = []
        self._text: list[str] = []
        self._cur: dict[str, str | int] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "body":
            self.in_body = True
            self.depth = 0
            return
        if not self.in_body:
            return
        if self.depth == 0 and tag not in SKIP_HTML_TAGS:
            self.even += 2
            self._cur = {"even": self.even, "tag": tag, "text": ""}
            self.kids.append(self._cur)
            self._text = []
        self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "body":
            self.in_body = False
            return
        if not self.in_body:
            return
        if self.depth == 1 and self._cur is not None:
            self._cur["text"] = " ".join(self._text).strip()
            self._cur = None
            self._text = []
        if self.depth > 0:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.in_body and self.depth >= 1 and data.strip():
            self._text.append(data.strip())


def newest_sqlite(directory: Path) -> Path:
    if not directory.is_dir():
        raise FileNotFoundError(
            f"Apple Books folder not found: {directory}\n"
            "Open Books once on this Mac so annotations sync locally."
        )
    files = sorted(
        (
            path
            for path in directory.glob("*.sqlite")
            if path.is_file() and not path.name.endswith(("-shm", "-wal"))
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not files:
        raise FileNotFoundError(f"No .sqlite database in {directory}")
    return files[0]


def open_ro(path: Path) -> sqlite3.Connection:
    uri = path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


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


def humanize_chapter_id(chapter_id: str, book_title: str | None = None) -> str:
    text = chapter_id.strip()
    if re.fullmatch(r"id\d+", text, flags=re.I):
        return text
    base, sep, suffix = text.rpartition("-")
    if sep and suffix.isdigit():
        if book_title and title_key(base) == title_key(book_title):
            return f"Section {suffix}"
        base_h = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", base)
        return f"{base_h} — {suffix}"
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)


def parse_cfi_chapter(location: str | None) -> tuple[int, str]:
    if not location:
        return (10**9, "unknown")
    m = CFI_SPINE_RE.search(location)
    if not m:
        return (10**9, "unknown")
    spine_n = int(m.group(1))
    cfi_id = (m.group(2) or "").strip()
    return (spine_n, cfi_id or f"spine-{spine_n}")


def parse_cfi_path_order(location: str | None) -> int:
    if not location:
        return 10**9
    m = CFI_PATH_RE.search(location)
    return int(m.group(1)) if m else 10**9


def paragraph_key(location: str | None) -> str:
    if not location:
        return "unknown"
    m = re.match(r"(epubcfi\([^,]+)", location)
    return m.group(1) if m else location


def merge_same_paragraph(highlights: list[Highlight]) -> list[Highlight]:
    if not highlights:
        return []
    merged: list[Highlight] = []
    current = highlights[0]
    parts = [current.text.strip()]
    notes = [current.note] if current.note else []

    def flush() -> None:
        nonlocal current, parts, notes
        text = " — ".join(p for p in parts if p)
        note = " | ".join(n for n in notes if n) or None
        merged.append(
            Highlight(
                text=text,
                note=note,
                style=current.style,
                created=current.created,
                modified=current.modified,
                location=current.location,
                range_start=current.range_start,
            )
        )

    for h in highlights[1:]:
        if paragraph_key(h.location) == paragraph_key(current.location):
            parts.append(h.text.strip())
            if h.note:
                notes.append(h.note)
            continue
        flush()
        current = h
        parts = [current.text.strip()]
        notes = [current.note] if current.note else []
    flush()
    return merged


def _norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _looks_like_prose(text: str) -> bool:
    if len(text) > 70:
        return True
    words = text.split()
    if not words:
        return True
    if text.endswith((".", ";", ",")) and len(words) > 6:
        return True
    if len(words) > 8:
        return True
    # Epigraph / body openers often follow CHAPTER titles in this EPUB
    if words[0] in {
        "They",
        "He",
        "She",
        "We",
        "I",
        "You",
        "It",
        "There",
        "Here",
        "A",
        "An",
        "And",
        "But",
        "If",
        "When",
        "As",
    } and len(words) >= 4:
        return True
    return False


def extract_topics_from_html(html: str, book_title: str) -> list[tuple[int, str]]:
    """Return [(cfi_path_even, topic_title), ...] in document order."""
    parser = _BodyChildrenParser()
    try:
        parser.feed(html)
    except Exception:
        return []

    topics: list[tuple[int, str]] = []
    for kid in parser.kids:
        tag = str(kid["tag"])
        text = _norm_space(str(kid["text"]))
        if tag in {"h1", "h2", "h3"} and text:
            topics.append((int(kid["even"]), text))
            break

    i = 0
    kids = parser.kids
    while i < len(kids):
        letters: list[str] = []
        j = i
        while j < len(kids):
            t = _norm_space(str(kids[j]["text"]))
            if len(t) == 1 and t.isalpha():
                letters.append(t.upper())
                j += 1
                continue
            break
        if "".join(letters) != "CHAPTER":
            i += 1
            continue

        start_even = int(kids[i]["even"])
        title_parts: list[str] = []
        while j < len(kids):
            t = _norm_space(str(kids[j]["text"]))
            j += 1
            if not t:
                continue
            if t.startswith("PC-") or re.fullmatch(r"\d+", t):
                continue
            if title_key(t) == title_key(book_title):
                continue
            if _looks_like_prose(t):
                break
            # Once we already have a usable title, only allow short continuations
            joined_so_far = " ".join(title_parts)
            if title_parts and len(joined_so_far.split()) >= 3 and len(t.split()) > 3:
                break
            title_parts.append(t)
            joined = " ".join(title_parts)
            if len(joined) > 55 or len(joined.split()) >= 6 or len(title_parts) >= 4:
                break

        title = " ".join(title_parts).strip(" :")
        if title:
            topics.append((start_even, title))
        i = j

    deduped: list[tuple[int, str]] = []
    for even, title in topics:
        if deduped and deduped[-1][1] == title:
            continue
        deduped.append((even, title))
    return deduped


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def load_library(lib_path: Path) -> dict[str, tuple[str, str, str | None]]:
    meta: dict[str, tuple[str, str, str | None]] = {}
    with open_ro(lib_path) as conn:
        rows = conn.execute(
            """
            SELECT ZASSETID, ZTEMPORARYASSETID, ZTITLE, ZAUTHOR, ZPATH
            FROM ZBKLIBRARYASSET
            WHERE ZTITLE IS NOT NULL AND TRIM(ZTITLE) != ''
            """
        )
        for row in rows:
            title = (row["ZTITLE"] or "").strip()
            author = (row["ZAUTHOR"] or "").strip() or "Unknown"
            path = (row["ZPATH"] or "").strip() or None
            payload = (title, author, path)
            if row["ZASSETID"]:
                meta[row["ZASSETID"]] = payload
            if row["ZTEMPORARYASSETID"]:
                meta[row["ZTEMPORARYASSETID"]] = payload
    return meta


def load_highlights(ann_path: Path) -> dict[str, list[Highlight]]:
    by_asset: dict[str, list[Highlight]] = defaultdict(list)
    with open_ro(ann_path) as conn:
        rows = conn.execute(
            """
            SELECT
              ZANNOTATIONASSETID,
              ZANNOTATIONSELECTEDTEXT,
              ZANNOTATIONNOTE,
              ZANNOTATIONSTYLE,
              ZANNOTATIONCREATIONDATE,
              ZANNOTATIONMODIFICATIONDATE,
              ZANNOTATIONLOCATION,
              ZPLLOCATIONRANGESTART
            FROM ZAEANNOTATION
            WHERE ZANNOTATIONDELETED = 0
              AND ZANNOTATIONSELECTEDTEXT IS NOT NULL
              AND TRIM(ZANNOTATIONSELECTEDTEXT) != ''
            ORDER BY
              ZPLLOCATIONRANGESTART ASC,
              ZANNOTATIONCREATIONDATE ASC
            """
        )
        for row in rows:
            asset_id = row["ZANNOTATIONASSETID"]
            if not asset_id:
                continue
            text = (row["ZANNOTATIONSELECTEDTEXT"] or "").strip()
            note = (row["ZANNOTATIONNOTE"] or "").strip() or None
            by_asset[asset_id].append(
                Highlight(
                    text=text,
                    note=note,
                    style=row["ZANNOTATIONSTYLE"],
                    created=row["ZANNOTATIONCREATIONDATE"],
                    modified=row["ZANNOTATIONMODIFICATIONDATE"],
                    location=row["ZANNOTATIONLOCATION"],
                    range_start=row["ZPLLOCATIONRANGESTART"],
                )
            )
    return by_asset


def find_local_epub(title: str, library_path: str | None) -> Path | None:
    candidates: list[Path] = []
    if library_path:
        p = Path(library_path)
        if p.is_file() and p.suffix.lower() == ".epub":
            candidates.append(p)
    if BOOKS_DIR.is_dir():
        q = normalize(title)
        for path in BOOKS_DIR.glob("*.epub"):
            if q and q in normalize(path.stem):
                candidates.append(path)
    for path in candidates:
        try:
            if path.stat().st_size < 1024:
                continue
            with zipfile.ZipFile(path) as zf:
                if zf.namelist():
                    return path
        except (OSError, zipfile.BadZipFile, PermissionError):
            continue
    return None


def load_epub_spine(epub_path: Path) -> list[tuple[str, str, str]]:
    """Return [(item_id, href, zip_path), ...] in spine order."""
    spine: list[tuple[str, str, str]] = []
    try:
        with zipfile.ZipFile(epub_path) as zf:
            container = ET.fromstring(zf.read("META-INF/container.xml"))
            opf_path = None
            for node in container.iter():
                if _local(node.tag) == "rootfile":
                    opf_path = node.attrib.get("full-path")
                    break
            if not opf_path:
                return spine
            opf_dir = str(Path(opf_path).parent)
            if opf_dir == ".":
                opf_dir = ""
            opf = ET.fromstring(zf.read(opf_path))
            items: dict[str, str] = {}
            for node in opf.iter():
                if _local(node.tag) == "item":
                    item_id = node.attrib.get("id")
                    href = node.attrib.get("href")
                    if item_id and href:
                        items[item_id] = href
            for node in opf.iter():
                if _local(node.tag) != "itemref":
                    continue
                item_id = node.attrib.get("idref")
                if not item_id or item_id not in items:
                    continue
                href = items[item_id]
                zip_path = f"{opf_dir}/{href}" if opf_dir else href
                zip_path = zip_path.replace("\\", "/").lstrip("./")
                spine.append((item_id, href, zip_path))
    except (OSError, zipfile.BadZipFile, ET.ParseError, PermissionError, KeyError):
        return []
    return spine


def load_epub_chapter_titles(epub_path: Path) -> dict[str, str]:
    titles: dict[str, str] = {}
    try:
        with zipfile.ZipFile(epub_path) as zf:
            names = zf.namelist()
            container = ET.fromstring(zf.read("META-INF/container.xml"))
            opf_path = None
            for node in container.iter():
                if _local(node.tag) == "rootfile":
                    opf_path = node.attrib.get("full-path")
                    break
            if not opf_path:
                return titles
            opf = ET.fromstring(zf.read(opf_path))
            items: dict[str, str] = {}
            for node in opf.iter():
                if _local(node.tag) == "item":
                    item_id = node.attrib.get("id")
                    href = node.attrib.get("href")
                    if item_id and href:
                        items[item_id] = href
                        titles[item_id] = item_id
            ncx_name = next((n for n in names if n.endswith(".ncx")), None)
            if not ncx_name:
                return titles
            ncx = ET.fromstring(zf.read(ncx_name))
            for nav in ncx.iter():
                if _local(nav.tag) != "navPoint":
                    continue
                label = None
                src = None
                for child in nav:
                    lname = _local(child.tag)
                    if lname == "navLabel":
                        for text_node in child.iter():
                            if _local(text_node.tag) == "text" and text_node.text:
                                label = text_node.text.strip()
                    elif lname == "content":
                        src = child.attrib.get("src")
                if label and src:
                    href = src.split("#", 1)[0]
                    stem = Path(href).stem
                    titles[stem] = label
                    titles[href] = label
                    for item_id, item_href in items.items():
                        if item_href == href or Path(item_href).stem == stem:
                            titles[item_id] = label
    except (OSError, zipfile.BadZipFile, ET.ParseError, PermissionError, KeyError):
        return titles
    return titles


def build_topic_index(
    epub_path: Path | None,
    book_title: str,
    toc: dict[str, str],
) -> dict[str, list[tuple[int, str]]]:
    """spine_key → [(path_even, topic_title), ...]"""
    index: dict[str, list[tuple[int, str]]] = {}
    if not epub_path:
        return index
    try:
        with zipfile.ZipFile(epub_path) as zf:
            for item_id, href, zip_path in load_epub_spine(epub_path):
                try:
                    html = zf.read(zip_path).decode("utf-8", errors="replace")
                except KeyError:
                    continue
                topics = extract_topics_from_html(html, book_title)
                if not topics:
                    fallback = toc.get(item_id) or toc.get(Path(href).stem)
                    if fallback and fallback != item_id:
                        topics = [(0, fallback)]
                if topics:
                    index[item_id] = topics
    except (OSError, zipfile.BadZipFile, PermissionError):
        return index
    return index


def resolve_topic(
    highlight: Highlight,
    topic_index: dict[str, list[tuple[int, str]]],
    toc: dict[str, str],
    book_title: str,
) -> TopicInfo:
    spine_n, spine_key = parse_cfi_chapter(highlight.location)
    path_even = parse_cfi_path_order(highlight.location)

    topics = topic_index.get(spine_key) or []
    if topics:
        title = topics[0][1]
        topic_even = topics[0][0]
        for even, candidate in topics:
            if even <= path_even:
                title = candidate
                topic_even = even
            else:
                break
        return TopicInfo(
            key=f"{spine_key}:{topic_even}:{title}",
            title=title,
            order=(spine_n, topic_even),
        )

    title = toc.get(spine_key) or humanize_chapter_id(spine_key, book_title)
    if spine_key not in toc:
        for toc_key, toc_title in toc.items():
            if spine_key.endswith(toc_key) or toc_key.endswith(spine_key):
                title = toc_title
                break
    return TopicInfo(
        key=f"{spine_key}:0:{title}",
        title=title,
        order=(spine_n, 0),
    )


def build_exports(
    library: dict[str, tuple[str, str, str | None]],
    by_asset: dict[str, list[Highlight]],
) -> list[BookExport]:
    exports: list[BookExport] = []
    for asset_id, highlights in by_asset.items():
        title, author, path = library.get(
            asset_id, (f"Untitled {asset_id[:8]}", "Unknown", None)
        )
        exports.append(
            BookExport(
                asset_id=asset_id,
                title=title,
                author=author,
                path=path,
                highlights=highlights,
            )
        )
    exports.sort(key=lambda book: book.title.lower())
    return exports


def filter_books(exports: list[BookExport], query: str | None) -> list[BookExport]:
    if not query:
        return exports
    raw = query.strip()
    q = normalize(raw)
    q_id = re.sub(r"[^a-f0-9]", "", raw.lower())

    if q_id and len(q_id) >= 4:
        exact = [book for book in exports if book.asset_id.lower() == q_id]
        if len(exact) == 1:
            return exact
        if len(exact) > 1:
            raise ValueError(f"Multiple books with asset id {raw!r}")
        prefix = [book for book in exports if book.asset_id.lower().startswith(q_id)]
        if len(prefix) == 1:
            return prefix
        if len(prefix) > 1:
            opts = ", ".join(f"{b.asset_id[:8]} {b.title}" for b in prefix[:10])
            raise ValueError(f"Ambiguous book id prefix {raw!r}: {opts}")

    matched = [
        book
        for book in exports
        if q in normalize(book.title)
        or q in normalize(book.author)
        or (q_id and q_id in book.asset_id.lower())
    ]
    if not matched:
        available = ", ".join(
            f"{b.asset_id[:8]} {b.title} ({len(b.highlights)})" for b in exports[:20]
        )
        raise ValueError(f"No book matched {query!r}. Examples: {available}")
    return matched


def group_by_topic(book: BookExport) -> list[tuple[TopicInfo, list[Highlight]]]:
    epub = find_local_epub(book.title, book.path)
    toc = load_epub_chapter_titles(epub) if epub else {}
    topic_index = build_topic_index(epub, book.title, toc)

    topic_map: dict[str, TopicInfo] = {}
    grouped: dict[str, dict[str, list[Highlight]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for h in book.highlights:
        topic = resolve_topic(h, topic_index, toc, book.title)
        topic_map[topic.key] = topic
        grouped[topic.key][bucket_for(h.style)].append(h)

    keys = sorted(topic_map.keys(), key=lambda k: topic_map[k].order)
    result: list[tuple[TopicInfo, list[Highlight]]] = []
    for key in keys:
        by_label = grouped[key]
        merged_all: list[Highlight] = []
        for _label, items in by_label.items():
            items.sort(
                key=lambda h: (
                    h.range_start if h.range_start is not None else 10**9,
                    parse_cfi_path_order(h.location),
                    h.created or 0,
                )
            )
            merged_all.extend(merge_same_paragraph(items))
        merged_all.sort(
            key=lambda h: (
                h.range_start if h.range_start is not None else 10**9,
                parse_cfi_path_order(h.location),
                h.created or 0,
            )
        )
        result.append((topic_map[key], merged_all))
    return result


def render_highlight(h: Highlight) -> list[str]:
    # Green → important chapter/theme heading
    if h.style == 1:
        return [f"### {h.text}", ""]
    # Purple → bold insight
    if h.style == 5:
        lines = [f"- **{h.text}**"]
    else:
        label = bucket_for(h.style)
        lines = [f"- [{label}] {h.text}"]
    if h.note:
        lines.append(f"  - note: {h.note}")
    return lines


def render_markdown(book: BookExport) -> str:
    groups = group_by_topic(book)
    lines = [
        "---",
        f'title: "{book.title.replace(chr(34), chr(39))}"',
        f'author: "{book.author.replace(chr(34), chr(39))}"',
        f"asset_id: {book.asset_id}",
        f"highlights: {len(book.highlights)}",
        f"exported: {datetime.now(tz=timezone.utc).date().isoformat()}",
        "source: apple-books",
        "labels: green→theme heading; purple→bold; yellow→info; pink→insights; blue→how",
        "---",
        "",
        f"# {book.title}",
        "",
        f"*{book.author}*",
        "",
        "> Grouped by book topics. Green → ### theme; purple → **bold**; pink → [insights]; blue → [how]; yellow → [info].",
        "",
    ]
    for topic, items in groups:
        if not items:
            continue
        # If the only/first item is green matching the chapter title, skip duplicate ##
        lines.append(f"## {topic.title}")
        lines.append("")
        for h in items:
            # Skip green bullet that merely repeats the chapter heading
            if (
                h.style == 1
                and title_key(h.text) == title_key(topic.title)
            ):
                continue
            rendered = render_highlight(h)
            lines.extend(rendered)
            if h.style != 1:
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_exports(exports: list[BookExport], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=timezone.utc).date().isoformat()
    written: list[Path] = []
    for book in exports:
        path = out_dir / f"{today}-{slugify(book.title)}.md"
        path.write_text(render_markdown(book), encoding="utf-8")
        written.append(path)
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Apple Books highlights to notes/ (by book topic + color labels)."
    )
    parser.add_argument(
        "book",
        nargs="?",
        help="Title, author, or Apple Books asset id / prefix (example: E5527B46)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List books with highlight counts; do not write files",
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
        ann_path = newest_sqlite(ANNOTATION_DIR)
        lib_path = newest_sqlite(LIBRARY_DIR)
        library = load_library(lib_path)
        by_asset = load_highlights(ann_path)
        exports = filter_books(build_exports(library, by_asset), args.book)
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if isinstance(exc, sqlite3.Error):
            print(
                "Tip: grant Full Disk Access to Terminal/Cursor if Books DBs are blocked.",
                file=sys.stderr,
            )
        return 1

    if args.list:
        total = sum(len(book.highlights) for book in exports)
        print(f"{len(exports)} books, {total} highlights\n")
        for book in exports:
            print(
                f"{len(book.highlights):5}  {book.asset_id[:8]}  {book.title} — {book.author}"
            )
        return 0

    written = write_exports(exports, args.output)
    total = sum(len(book.highlights) for book in exports)
    print(f"Wrote {len(written)} file(s), {total} highlights → {args.output}")
    for path in written:
        print(f"  {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
