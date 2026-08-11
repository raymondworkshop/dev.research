#!/usr/bin/env python3
"""Export Kindle app / Cloud Reader highlights to notes/ as Markdown.

Kindle app (iOS/Android) and Cloud Reader sync highlights to Amazon Notebook:
  https://read.amazon.com/notebook

This script pulls that Notebook (same place the app syncs to).

Auth (first match):
  1. --cookies / $KINDLE_COOKIES / ~/.config/dev.research/kindle-cookies.txt
  2. Browser cookies via browser-cookie3 (Chrome / Safari / Firefox / Edge)
     → sign in once at https://read.amazon.com/notebook in that browser

Fallback: --clippings for a physical Kindle My Clippings.txt

Color labels (Kindle swatches → books-export buckets):
  yellow → [info] · blue → [how] · pink → [insights] · orange → **bold**

Usage:
  make kindle-export LIST=1
  make kindle-export BOOK='Psychology of Money'
  make kindle-export CLIPPINGS='~/My Clippings.txt' BOOK='…'
"""
from __future__ import annotations

import argparse
import http.cookiejar
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "notes"
DEFAULT_COOKIES = Path.home() / ".config/dev.research/kindle-cookies.txt"
DEFAULT_DOMAIN = "amazon.com"

# Kindle color → Apple Books ZANNOTATIONSTYLE-style bucket
COLOR_STYLE = {
    "yellow": 3,  # info
    "blue": 2,  # how
    "pink": 4,  # insights
    "orange": 5,  # bold (purple bucket)
}

STYLE_BUCKET = {
    1: "important",
    2: "how",
    3: "info",
    4: "insights",
    5: "insights",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# My Clippings: "Title (Author)" — author is last (...) group
TITLE_AUTHOR_RE = re.compile(r"^(?P<title>.+?)\s+\((?P<author>[^)]+)\)\s*$")
META_RE = re.compile(
    r"-\s*(?:Your\s+)?(?P<kind>Highlight|Note|Bookmark|Clip)"
    r".*?"
    r"(?:page\s+(?P<page>[\d,]+))?.*?"
    r"(?:[Ll]ocation|位置)\s*(?P<loc_start>\d+)(?:-(?P<loc_end>\d+))?.*?"
    r"(?:Added on\s+(?P<added>.+))?\s*$",
    re.IGNORECASE | re.DOTALL,
)
LOC_ONLY_RE = re.compile(
    r"-\s*(?:Your\s+)?(?P<kind>Highlight|Note|Bookmark|Clip)"
    r".*?(?:[Ll]ocation|位置)\s*(?P<loc_start>\d+)(?:-(?P<loc_end>\d+))?",
    re.IGNORECASE | re.DOTALL,
)
ASIN_RE = re.compile(r"\b([A-Z0-9]{10})\b")
COLOR_CLASS_RE = re.compile(
    r"kp-notebook-highlight[^\s\"']*?(yellow|blue|pink|orange)",
    re.IGNORECASE,
)


@dataclass
class Highlight:
    text: str
    note: str | None = None
    style: int | None = None
    location: str | None = None
    page: int | None = None
    loc_start: int | None = None
    kind: str = "highlight"


@dataclass
class BookExport:
    asin: str
    title: str
    author: str
    highlights: list[Highlight] = field(default_factory=list)


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


def _norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# --- cookies -----------------------------------------------------------------


def load_cookie_jar(path: Path) -> http.cookiejar.MozillaCookieJar:
    if not path.is_file():
        raise FileNotFoundError(f"Cookie file not found: {path}")
    jar = http.cookiejar.MozillaCookieJar(str(path))
    # ignore_discard / ignore_expires: Amazon session cookies are often session-only
    jar.load(ignore_discard=True, ignore_expires=True)
    return jar


def cookie_header_from_pairs(pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        raise ValueError("No Amazon cookies available.")
    # Dedup by name (last wins)
    by_name: dict[str, str] = {}
    for name, value in pairs:
        by_name[name] = value
    return "; ".join(f"{k}={v}" for k, v in by_name.items())


def cookie_header(jar: http.cookiejar.CookieJar, domain: str) -> str:
    """Build Cookie header for read.<domain> / .<domain>."""
    host = f"read.{domain}"
    parts: list[tuple[str, str]] = []
    for c in jar:
        if c.is_expired():
            continue
        d = (c.domain or "").lstrip(".").lower()
        if not d:
            continue
        if domain.lower() in d or d in host or host.endswith(d):
            parts.append((c.name, c.value))
    if not parts:
        for c in jar:
            d = (c.domain or "").lower()
            if "amazon" in d:
                parts.append((c.name, c.value))
    if not parts:
        raise ValueError(
            f"No Amazon cookies found in jar for domain {domain!r}. "
            "Re-export while signed in at read.amazon.com/notebook."
        )
    return cookie_header_from_pairs(pairs)


def load_browser_cookies(domain: str) -> list[tuple[str, str]]:
    """Return (browser_name, cookie_header) candidates from local browsers."""
    try:
        import browser_cookie3  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "browser-cookie3 not installed. "
            "Run: researchenv/bin/pip install browser-cookie3"
        ) from exc

    loaders = [
        ("chrome", getattr(browser_cookie3, "chrome", None)),
        ("chromium", getattr(browser_cookie3, "chromium", None)),
        ("safari", getattr(browser_cookie3, "safari", None)),
        ("firefox", getattr(browser_cookie3, "firefox", None)),
        ("edge", getattr(browser_cookie3, "edge", None)),
    ]
    errors: list[str] = []
    candidates: list[tuple[str, str]] = []

    for name, loader in loaders:
        if loader is None:
            continue
        try:
            jar = loader(domain_name=domain)
        except Exception as exc:  # noqa: BLE001 — try next browser
            errors.append(f"{name}: {exc}")
            continue
        pairs: list[tuple[str, str]] = []
        for c in jar:
            d = (c.domain or "").lower()
            if "amazon" not in d:
                continue
            pairs.append((c.name, c.value))
        if pairs:
            candidates.append((name, cookie_header_from_pairs(pairs)))
        else:
            errors.append(f"{name}: no amazon cookies")

    if candidates:
        return candidates

    detail = "; ".join(errors[:4]) if errors else "no browsers available"
    raise RuntimeError(
        "Could not load Amazon cookies from browsers. "
        f"Sign in at https://read.{domain}/notebook in Chrome/Safari, then retry. "
        f"({detail})"
    )


def looks_like_signin(html: str) -> bool:
    lower = html.lower()
    if "kp-notebook-library" in lower or 'id="kp-notebook' in lower:
        return False
    if "ap_signin" in lower or "auth-signin" in lower:
        return True
    head = lower[:3000]
    return "sign in" in head and "kp-notebook" not in lower


def resolve_cookie_header(domain: str, cookies_path: Path | None) -> str:
    """File cookies if present; otherwise first browser session that reaches Notebook."""
    path: Path | None = None
    if cookies_path is not None:
        path = cookies_path.expanduser()
    else:
        env_path = os.environ.get("KINDLE_COOKIES")
        if env_path:
            path = Path(env_path).expanduser()
        elif DEFAULT_COOKIES.is_file():
            path = DEFAULT_COOKIES

    if path is not None:
        if not path.is_file():
            raise FileNotFoundError(
                f"Cookie file not found: {path}\n"
                "Or omit --cookies to use your browser session "
                f"(sign in at https://read.{domain}/notebook first)."
            )
        print(f"Using cookie file {path}", file=sys.stderr)
        return cookie_header(load_cookie_jar(path), domain)

    base = f"https://read.{domain}/notebook"
    last_err: Exception | None = None
    for name, cookie in load_browser_cookies(domain):
        try:
            html = http_get(base, cookie)
        except RuntimeError as exc:
            last_err = exc
            print(f"Skip {name}: {exc}", file=sys.stderr)
            continue
        if looks_like_signin(html):
            print(
                f"Skip {name}: signed-out session — open {base} in {name} and sign in",
                file=sys.stderr,
            )
            continue
        print(f"Using {name} cookies for {domain}", file=sys.stderr)
        return cookie

    hint = f" Last error: {last_err}" if last_err else ""
    raise RuntimeError(
        f"No browser is signed in to Kindle Notebook ({base}). "
        "Open that URL in Chrome or Safari (same Amazon account as the Kindle app), "
        f"sign in, then run again.{hint}"
    )


def http_get(url: str, cookie: str, timeout: float = 45.0) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": cookie,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(
            f"HTTP {exc.code} for {url}\n{body}\n"
            "Tip: cookies expired — re-export from a browser session."
        ) from exc


# --- HTML parsing (Notebook) -------------------------------------------------


class _TagStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def text(self) -> str:
        return _norm_space("".join(self._parts))


def html_text(fragment: str) -> str:
    p = _TagStripper()
    try:
        p.feed(fragment)
        p.close()
    except Exception:  # noqa: BLE001 — broken fragments still yield partial text
        return _norm_space(re.sub(r"<[^>]+>", " ", fragment))
    return p.text()


def extract_attr_blocks(html: str, attr: str) -> list[tuple[str, str]]:
    """Return (attr_value, inner_or_tag) for tags carrying attr=..."""
    # data-get-annotations-for-asin='{"asin":"B0…"}'
    pat = re.compile(
        rf"""{re.escape(attr)}\s*=\s*(['"])(.*?)\1""",
        re.IGNORECASE | re.DOTALL,
    )
    return [(m.group(2), m.group(0)) for m in pat.finditer(html)]


def parse_library_asins(html: str) -> list[str]:
    asins: list[str] = []
    seen: set[str] = set()

    for raw, _ in extract_attr_blocks(html, "data-get-annotations-for-asin"):
        m = re.search(r"""["']asin["']\s*:\s*["']([A-Z0-9]{10})["']""", raw)
        if not m:
            m = ASIN_RE.search(raw.upper())
        if m:
            asin = m.group(1).upper()
            if asin not in seen:
                seen.add(asin)
                asins.append(asin)

    # Fallback: library row ids
    for m in re.finditer(
        r"""id=["']([A-Z0-9]{10})["'][^>]*class=["'][^"']*kp-notebook-library""",
        html,
        re.IGNORECASE,
    ):
        asin = m.group(1).upper()
        if asin not in seen:
            seen.add(asin)
            asins.append(asin)

    for m in re.finditer(
        r"""class=["'][^"']*kp-notebook-library-each-book[^"']*["'][^>]*id=["']([A-Z0-9]{10})["']""",
        html,
        re.IGNORECASE,
    ):
        asin = m.group(1).upper()
        if asin not in seen:
            seen.add(asin)
            asins.append(asin)

    return asins


def _style_from_highlight_html(chunk: str) -> int | None:
    m = COLOR_CLASS_RE.search(chunk)
    if m:
        return COLOR_STYLE.get(m.group(1).lower())
    # inline color hints
    lower = chunk.lower()
    for name, style in COLOR_STYLE.items():
        if name in lower and "highlight" in lower:
            return style
    return 3  # Kindle default yellow → info


def parse_annotations_html(html: str, asin: str) -> BookExport:
    title = "Untitled"
    author = "Unknown"

    h3 = re.search(r"<h3[^>]*>(.*?)</h3>", html, re.IGNORECASE | re.DOTALL)
    if h3:
        title = html_text(h3.group(1)) or title
        # author often follows in next sibling <p> / <span>
        after = html[h3.end() : h3.end() + 800]
        p = re.search(
            r"<(?:p|span|div)[^>]*>(.*?)</(?:p|span|div)>",
            after,
            re.IGNORECASE | re.DOTALL,
        )
        if p:
            maybe = html_text(p.group(1))
            if maybe and normalize(maybe) != normalize(title):
                author = maybe

    # Prefer annotations container; else whole doc
    container = html
    m_ann = re.search(
        r"""id=["']kp-notebook-annotations["'][^>]*>(.*)$""",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if m_ann:
        container = m_ann.group(1)

    highlights: list[Highlight] = []
    # Each annotation row
    rows = re.split(
        r"""(?i)<div[^>]*class=["'][^"']*a-row[^"']*a-spacing-base[^"']*["'][^>]*>""",
        container,
    )
    for row in rows[1:]:
        # stop at next major section if present
        row = row[:4000]
        hl_m = re.search(
            r"""(?is)<[^>]*id=["']highlight["'][^>]*>(.*?)</(?:span|div)>"""
            r"""|class=["'][^"']*kp-notebook-highlight[^"']*["'][^>]*>(.*?)</(?:span|div)>""",
            row,
        )
        if not hl_m:
            continue
        text = html_text(hl_m.group(1) or hl_m.group(2) or "")
        if not text or text.lower() in {"highlight", "loading"}:
            continue

        note: str | None = None
        note_m = re.search(
            r"""(?is)(?:id=["']note["']|kp-notebook-note)[^>]*>(.*?)</(?:span|div)>""",
            row,
        )
        if note_m:
            note_txt = html_text(note_m.group(1))
            # Notebook often prefixes "Note:"
            note_txt = re.sub(r"^(?:Note|笔记)\s*:?\s*", "", note_txt, flags=re.I)
            if note_txt and note_txt.lower() not in {"note", "loading", ""}:
                note = note_txt

        location = None
        page = None
        loc_start = None
        meta_m = re.search(
            r"""(?is)class=["'][^"']*kp-notebook-metadata[^"']*["'][^>]*>(.*?)</(?:span|div)>""",
            row,
        )
        if meta_m:
            meta = html_text(meta_m.group(1))
            location = meta or None
            pm = re.search(r"(?:page|页)\s*([\d,]+)", meta, re.I)
            if pm:
                page = int(pm.group(1).replace(",", ""))
            lm = re.search(r"(?:location|位置)\s*([\d,]+)", meta, re.I)
            if lm:
                loc_start = int(lm.group(1).replace(",", ""))

        style = _style_from_highlight_html(hl_m.group(0) + row[:500])
        highlights.append(
            Highlight(
                text=text,
                note=note,
                style=style,
                location=location,
                page=page,
                loc_start=loc_start,
            )
        )

    # Dedup exact text+location
    seen: set[tuple[str, str | None]] = set()
    uniq: list[Highlight] = []
    for h in highlights:
        key = (h.text, h.location)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)

    return BookExport(asin=asin, title=title, author=author, highlights=uniq)


def fetch_notebook_exports(
    domain: str,
    cookie: str,
    book_query: str | None,
) -> list[BookExport]:
    base = f"https://read.{domain}/notebook"
    lib_html = http_get(base, cookie)
    if "ap_signin" in lib_html.lower() or "sign in" in lib_html.lower()[:2000]:
        # soft check — notebook still has "Sign in" chrome sometimes
        if "kp-notebook" not in lib_html and "kp-notebook-library" not in lib_html:
            raise RuntimeError(
                "Amazon returned a sign-in page. Open "
                f"https://read.{domain}/notebook in your browser, sign in, then retry."
            )

    asins = parse_library_asins(lib_html)
    if not asins:
        raise RuntimeError(
            "No books found in Kindle Notebook. "
            "In the Kindle app: open a book → highlight → wait for sync, then check "
            f"https://read.{domain}/notebook"
        )

    exports: list[BookExport] = []
    for asin in asins:
        url = f"{base}?asin={asin}&contentLimitState=&"
        try:
            page = http_get(url, cookie)
        except RuntimeError as exc:
            print(f"WARN: skip {asin}: {exc}", file=sys.stderr)
            continue
        book = parse_annotations_html(page, asin)
        if not book.highlights:
            continue
        exports.append(book)

    return filter_books(exports, book_query)


# --- My Clippings.txt --------------------------------------------------------


def parse_title_author(line: str) -> tuple[str, str]:
    line = line.strip().lstrip("\ufeff")
    m = TITLE_AUTHOR_RE.match(line)
    if m:
        return m.group("title").strip(), m.group("author").strip()
    return line, "Unknown"


def parse_clippings(text: str) -> list[BookExport]:
    text = text.lstrip("\ufeff")
    blocks = re.split(r"\n==========\s*\n?", text)
    by_key: dict[tuple[str, str], BookExport] = {}
    pending_notes: dict[tuple[str, str, int | None], list[str]] = defaultdict(list)

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if len(lines) < 2:
            continue
        title, author = parse_title_author(lines[0])
        meta_line = lines[1].strip()
        body = "\n".join(lines[2:]).strip()
        kind_m = META_RE.search(meta_line) or LOC_ONLY_RE.search(meta_line)
        kind = (kind_m.group("kind") if kind_m else "Highlight").lower()
        page = None
        loc_start = None
        if kind_m:
            if "page" in kind_m.groupdict() and kind_m.groupdict().get("page"):
                page = int(kind_m.group("page").replace(",", ""))
            loc_start = int(kind_m.group("loc_start")) if kind_m.group("loc_start") else None

        key = (title_key(title), normalize(author))
        book = by_key.get(key)
        if book is None:
            book = BookExport(asin="", title=title, author=author, highlights=[])
            by_key[key] = book

        if kind == "bookmark" or not body:
            continue
        if kind == "note":
            pending_notes[(key[0], key[1], loc_start)].append(body)
            continue

        book.highlights.append(
            Highlight(
                text=_norm_space(body),
                note=None,
                style=3,
                location=meta_line.lstrip("- ").strip(),
                page=page,
                loc_start=loc_start,
                kind="highlight",
            )
        )

    # Attach notes that share a location with a highlight
    for book in by_key.values():
        bk = (title_key(book.title), normalize(book.author))
        for h in book.highlights:
            notes = pending_notes.get((bk[0], bk[1], h.loc_start))
            if notes:
                h.note = " | ".join(notes)
                pending_notes[(bk[0], bk[1], h.loc_start)] = []
        # orphan notes → standalone bullets
        for (t, a, loc), notes in list(pending_notes.items()):
            if (t, a) != bk or not notes:
                continue
            for n in notes:
                book.highlights.append(
                    Highlight(
                        text=n,
                        note=None,
                        style=3,
                        location=f"Note @ location {loc}" if loc else "Note",
                        loc_start=loc,
                        kind="note",
                    )
                )
            pending_notes[(t, a, loc)] = []

    return [b for b in by_key.values() if b.highlights]


def load_clippings_exports(path: Path, book_query: str | None) -> list[BookExport]:
    if not path.is_file():
        raise FileNotFoundError(f"Clippings file not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    return filter_books(parse_clippings(text), book_query)


# --- filter / render ---------------------------------------------------------


def filter_books(exports: list[BookExport], query: str | None) -> list[BookExport]:
    if not query:
        return sorted(exports, key=lambda b: b.title.lower())
    q = query.strip()
    qn = normalize(q)
    q_asin = q.upper()

    exact_asin = [b for b in exports if b.asin and b.asin.upper() == q_asin]
    if exact_asin:
        return exact_asin

    hits = [
        b
        for b in exports
        if qn in normalize(b.title)
        or qn in normalize(b.author)
        or (b.asin and b.asin.upper().startswith(q_asin))
        or q.lower() in b.title.lower()
    ]
    if not hits:
        sample = ", ".join(f"{b.title} ({len(b.highlights)})" for b in exports[:15])
        raise ValueError(f"No book matched {query!r}. Examples: {sample}")
    return sorted(hits, key=lambda b: b.title.lower())


def group_highlights(book: BookExport) -> list[tuple[str, list[Highlight]]]:
    """Group by page when present, else location band, else flat."""
    if not book.highlights:
        return []
    if any(h.page is not None for h in book.highlights):
        by_page: dict[int | None, list[Highlight]] = defaultdict(list)
        for h in book.highlights:
            by_page[h.page].append(h)
        groups: list[tuple[str, list[Highlight]]] = []
        for page in sorted(by_page, key=lambda p: (p is None, p or 0)):
            items = sorted(
                by_page[page],
                key=lambda h: (h.loc_start if h.loc_start is not None else 10**9, h.text),
            )
            label = f"Page {page}" if page is not None else "No page"
            groups.append((label, items))
        return groups

    # Single section
    items = sorted(
        book.highlights,
        key=lambda h: (h.loc_start if h.loc_start is not None else 10**9, h.text),
    )
    return [("Highlights", items)]


def render_highlight(h: Highlight) -> list[str]:
    if h.style == 1:
        return [f"### {h.text}", ""]
    if h.style == 5:
        lines = [f"- **{h.text}**"]
    elif h.style in STYLE_BUCKET and h.style != 3:
        lines = [f"- [{bucket_for(h.style)}] {h.text}"]
    elif h.style == 3:
        lines = [f"- [info] {h.text}"]
    else:
        lines = [f"- {h.text}"]
    if h.note:
        lines.append(f"  - note: {h.note}")
    if h.location and h.kind != "note":
        # keep location as quiet metadata only when useful and short
        pass
    return lines


def render_markdown(book: BookExport, source: str) -> str:
    groups = group_highlights(book)
    asin_line = f"asin: {book.asin}" if book.asin else None
    lines = [
        "---",
        f'title: "{book.title.replace(chr(34), chr(39))}"',
        f'author: "{book.author.replace(chr(34), chr(39))}"',
    ]
    if asin_line:
        lines.append(asin_line)
    lines.extend(
        [
            f"highlights: {len(book.highlights)}",
            f"exported: {datetime.now(tz=timezone.utc).date().isoformat()}",
            f"source: {source}",
            "labels: yellow→info; blue→how; pink→insights; orange→bold",
            "---",
            "",
            f"# {book.title}",
            "",
            f"*{book.author}*",
            "",
            "> Kindle export. Yellow → [info]; blue → [how]; pink → [insights]; orange → **bold**.",
            "",
        ]
    )
    for topic, items in groups:
        if not items:
            continue
        lines.append(f"## {topic}")
        lines.append("")
        for h in items:
            rendered = render_highlight(h)
            lines.extend(rendered)
            if h.style != 1:
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_exports(
    exports: Iterable[BookExport], out_dir: Path, source: str
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=timezone.utc).date().isoformat()
    written: list[Path] = []
    for book in exports:
        if not book.highlights:
            continue
        path = out_dir / f"{today}-{slugify(book.title)}.md"
        path.write_text(render_markdown(book, source), encoding="utf-8")
        written.append(path)
    return written


# --- CLI ---------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Export Kindle app / Cloud Reader highlights (via Amazon Notebook) to notes/."
        )
    )
    p.add_argument(
        "book",
        nargs="?",
        help="Title, author, or ASIN / prefix (example: B00…)",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="List books with highlight counts; do not write files",
    )
    p.add_argument(
        "--cookies",
        type=Path,
        default=None,
        help=f"Netscape cookies.txt (optional; else browser session or {DEFAULT_COOKIES})",
    )
    p.add_argument(
        "--domain",
        default=DEFAULT_DOMAIN,
        help=f"Amazon domain without scheme (default: {DEFAULT_DOMAIN})",
    )
    p.add_argument(
        "--clippings",
        type=Path,
        default=None,
        help="Parse My Clippings.txt instead of Notebook",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=OUT_DIR,
        help=f"Output directory (default: {OUT_DIR})",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.clippings:
            source = "kindle-clippings"
            exports = load_clippings_exports(args.clippings.expanduser(), args.book)
        else:
            source = "kindle-notebook"
            cookie = resolve_cookie_header(args.domain, args.cookies)
            exports = fetch_notebook_exports(args.domain, cookie, args.book)
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if not args.clippings:
            print(
                "\nKindle app → notes/:\n"
                "  1. Highlight in the Kindle app (same Amazon account)\n"
                "  2. Confirm sync at https://read.amazon.com/notebook\n"
                "  3. Stay signed in to Amazon in Chrome/Safari on this Mac\n"
                "  4. make kindle-export LIST=1\n"
                "  5. make kindle-export BOOK='Your Book Title'\n"
                f"\nOptional cookies file: {DEFAULT_COOKIES}\n"
                "Regional store: DOMAIN=amazon.co.jp make kindle-export LIST=1",
                file=sys.stderr,
            )
        return 1

    if args.list:
        total = sum(len(b.highlights) for b in exports)
        print(f"{len(exports)} books, {total} highlights  [{source}]\n")
        for book in exports:
            asin = (book.asin or "-").ljust(10)
            print(f"{len(book.highlights):5}  {asin}  {book.title} — {book.author}")
        return 0

    if not exports:
        print("No books with highlights found.")
        return 1

    written = write_exports(exports, args.output, source)
    total = sum(len(b.highlights) for b in exports)
    print(f"Wrote {len(written)} file(s), {total} highlights → {args.output}")
    for path in written:
        try:
            print(f"  {path.relative_to(ROOT)}")
        except ValueError:
            print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
