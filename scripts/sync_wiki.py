#!/usr/bin/env python3
"""Compile notes/ → wiki/ via the local-gateway LLM (dev.local-ai).

Usage:
  python scripts/sync_wiki.py notes/2026-07-30-the-power-of-charm-….md
  python scripts/sync_wiki.py notes/….md --themes listening,eye-contact,charm
  python scripts/sync_wiki.py notes/….md --dry   # write to outputs/sync-draft/
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from config import (  # noqa: E402
    LLM_API_BASE,
    LLM_API_KEY,
    LLM_FALLBACK_ENABLED,
    LLM_FALLBACK_MODELS,
    LLM_MODEL,
    LLM_PROVIDER,
    NOTES_DIR,
    WIKI_DIR,
    llm_enabled,
)

INDEX = WIKI_DIR / "INDEX.md"
DRAFT_DIR = ROOT / "outputs" / "sync-draft"
FILE_RE = re.compile(
    r"===FILE:\s*(wiki/[^\s=]+?)\s*===\s*\n(.*?)(?=\n===FILE:|\Z)",
    re.S,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compile a note into wiki/ via LLM gateway.")
    p.add_argument(
        "note",
        nargs="?",
        help="Path to a note under notes/ (required unless --prompt-only)",
    )
    p.add_argument(
        "--themes",
        default="",
        help="Comma-separated theme slugs/titles (e.g. listening,eye-contact,charm)",
    )
    p.add_argument(
        "--dry",
        action="store_true",
        help="Write under outputs/sync-draft/ instead of wiki/",
    )
    p.add_argument(
        "--prompt-only",
        action="store_true",
        help="Print the compile prompt; do not call the LLM",
    )
    p.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="max_tokens for the completion (default 4096)",
    )
    return p.parse_args()


def parse_themes(raw: str) -> list[str]:
    themes: list[str] = []
    for part in raw.split(","):
        t = part.strip()
        if not t:
            continue
        themes.append(t)
    return themes


def theme_slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^\w\s-]+", "", s, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s or "theme"


def resolve_note(raw: str | None) -> Path:
    if not raw:
        raise ValueError("NOTE path required (example: notes/2026-07-30-….md)")
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Note not found: {path}")
    try:
        path.relative_to(NOTES_DIR.resolve())
    except ValueError as exc:
        raise ValueError(f"Note must be under notes/: {path}") from exc
    return path


def build_prompt(note_path: Path, themes: list[str]) -> str:
    index = INDEX.read_text(encoding="utf-8") if INDEX.is_file() else "(empty)"
    note = note_path.read_text(encoding="utf-8")
    rel = note_path.relative_to(ROOT)
    if len(note) > 60_000:
        note = note[:60_000] + "\n\n[…truncated…]"

    if themes:
        theme_lines = "\n".join(f"- {t} → wiki/{theme_slug(t)}.md" for t in themes)
        themes_block = f"""## Themes (exact pages only)
{theme_lines}
File onto these + wiki/INDEX.md. No extra pages unless nothing fits (note in INDEX). Prefer merge over near-duplicates."""
    else:
        themes_block = """## Themes (from note signals)
- Prefer `###` as pages; `**bold**` / `[insights]` = suggestions (merge/rename/drop OK).
- `[how]` → ### Actions on a theme (not its own page). `[info]` → detail under a theme.
- kebab-case filenames; merge into existing INDEX themes when they fit."""

    return f"""Compile note → wiki theme pages.

## Rules
- Never modify notes/. Wiki only: curated pages, not a highlight dump.
- Strip export labels (`[info]` `[insights]` `[how]`); keep author meaning; do not invent quotes.
- AI prose (intro/merge/framing): prefix `[AI Synthesis]:` on that line.
- Cite #### reference (prefer books/…) then note path. No chapter summaries/quizzes.
- Signals: ### = theme; **bold**/[insights] = theme suggestions; [how] = Actions; [info] = detail.
- Page: `[AI Synthesis]:` intro → ### sections → ### Actions → ## Sources → ## Related Topics
- [[wikilinks]] between themes. Always emit updated wiki/INDEX.md. Flag contradictions briefly if needed.

{themes_block}

## Output (only ===FILE=== blocks)
===FILE: wiki/theme-slug.md===
…
===FILE: wiki/INDEX.md===
…

## wiki/INDEX.md (current)
{index}

## Note
Path: {rel}

{note}
"""


def models_to_try() -> list[str]:
    models = [LLM_MODEL]
    if LLM_FALLBACK_ENABLED:
        for m in LLM_FALLBACK_MODELS:
            if m and m not in models:
                models.append(m)
    return models


def _fmt_secs(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    return f"{s // 60}m{s % 60:02d}s"


def call_llm(prompt: str, max_tokens: int) -> str:
    import threading
    import time

    import httpx

    if not llm_enabled():
        raise RuntimeError(
            f"LLM not enabled (provider={LLM_PROVIDER!r}). "
            "Check LLM_URL / LLM_MODEL in .env.development."
        )
    if not LLM_API_BASE:
        raise RuntimeError("LLM_API_BASE empty — set LLM_URL or LLM_API_BASE.")

    url = f"{LLM_API_BASE.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    prompt_chars = len(prompt)
    print(
        f"LLM provider={LLM_PROVIDER} base={LLM_API_BASE} "
        f"models={models_to_try()} max_tokens={max_tokens}",
        flush=True,
    )
    print(f"Prompt size≈{prompt_chars:,} chars (~{prompt_chars // 4:,} tokens est.)", flush=True)

    last_err: Exception | None = None
    for model in models_to_try():
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You compile notes into wiki markdown files. Output only ===FILE=== blocks.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stream": False,  # local-gateway does not support streaming
        }
        try:
            print(f"→ Calling {url}", flush=True)
            print(
                f"  model={model} stream=false "
                f"(gemma4 can take several minutes; heartbeat every 15s)",
                flush=True,
            )
            started = time.monotonic()
            stop_hb = threading.Event()

            def heartbeat() -> None:
                while not stop_hb.wait(15.0):
                    elapsed = _fmt_secs(time.monotonic() - started)
                    print(f"  … still waiting on {model} ({elapsed})", flush=True)

            hb = threading.Thread(target=heartbeat, daemon=True)
            hb.start()
            try:
                timeout = httpx.Timeout(600.0, connect=15.0)
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code >= 400:
                        body = resp.text[:500]
                        raise RuntimeError(f"HTTP {resp.status_code}: {body}")
                    data = resp.json()
            finally:
                stop_hb.set()

            text = data["choices"][0]["message"]["content"]
            elapsed = time.monotonic() - started
            usage = data.get("usage") or {}
            usage_bits = []
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if key in usage:
                    usage_bits.append(f"{key}={usage[key]}")
            usage_s = f" ({', '.join(usage_bits)})" if usage_bits else ""
            if not (text or "").strip():
                raise RuntimeError(f"Empty response from model={model}")
            print(
                f"  done model={model} in {_fmt_secs(elapsed)} "
                f"({len(text):,} chars){usage_s}",
                flush=True,
            )
            return text
        except Exception as exc:
            last_err = exc
            print(f"  failed ({model}): {exc}", flush=True)
            if LLM_FALLBACK_ENABLED and model != models_to_try()[-1]:
                print("  trying fallback model…", flush=True)
    raise RuntimeError(f"All models failed: {last_err}")


def parse_files(text: str) -> dict[str, str]:
    files = {m.group(1).strip(): m.group(2).strip() + "\n" for m in FILE_RE.finditer(text)}
    if not files:
        raise ValueError(
            "No ===FILE: wiki/…=== blocks in model output. "
            "Raw response saved for debugging if --dry."
        )
    return files


def write_files(files: dict[str, str], *, dry: bool) -> list[Path]:
    written: list[Path] = []
    for rel, body in files.items():
        if not rel.startswith("wiki/") or ".." in rel:
            print(f"  skip unsafe path: {rel}", flush=True)
            continue
        dest = (DRAFT_DIR / rel) if dry else (ROOT / rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")
        written.append(dest)
        print(f"  wrote {dest.relative_to(ROOT)}", flush=True)
    return written


def main() -> int:
    args = parse_args()
    try:
        if args.prompt_only and not args.note:
            # Generic prompt without a note body
            print("Compile notes → wiki/ per AGENTS.md.")
            print("Pass NOTE=notes/….md for a focused compile.")
            return 0
        note = resolve_note(args.note)
        themes = parse_themes(args.themes)
        note_rel = note.relative_to(ROOT)
        note_bytes = note.stat().st_size
        print(f"Note: {note_rel} ({note_bytes:,} bytes)", flush=True)
        if themes:
            print(
                "Themes: "
                + ", ".join(f"{t}→wiki/{theme_slug(t)}.md" for t in themes),
                flush=True,
            )
        else:
            print("Themes: auto from ### / **bold** / [insights]", flush=True)
        if args.dry:
            print("Mode: DRY → outputs/sync-draft/", flush=True)
        else:
            print("Mode: write wiki/", flush=True)
        print("Building prompt…", flush=True)
        prompt = build_prompt(note, themes)
        if args.prompt_only:
            print(prompt)
            return 0

        text = call_llm(prompt, args.max_tokens)
        print("Parsing ===FILE=== blocks…", flush=True)
        if args.dry:
            DRAFT_DIR.mkdir(parents=True, exist_ok=True)
            raw_path = DRAFT_DIR / "raw-response.md"
            raw_path.write_text(text, encoding="utf-8")
            print(f"  saved raw → {raw_path.relative_to(ROOT)}", flush=True)

        files = parse_files(text)
        print(f"Found {len(files)} file block(s)", flush=True)
        written = write_files(files, dry=args.dry)
        if not written:
            return 1
        print(f"Done: {len(written)} file(s)" + (" (dry)" if args.dry else ""), flush=True)
        return 0
    except (ValueError, FileNotFoundError, RuntimeError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # httpx errors without importing httpx at module level
        if type(exc).__module__.startswith("httpx"):
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        raise


if __name__ == "__main__":
    raise SystemExit(main())
