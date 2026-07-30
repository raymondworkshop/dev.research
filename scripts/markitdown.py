#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "books"
SCRIPT_DIR = Path(__file__).resolve().parent

# Avoid shadowing the installed `markitdown` package with this wrapper file.
sys.path = [path for path in sys.path if Path(path or ".").resolve() != SCRIPT_DIR]


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def convertible_books() -> list[Path]:
    return sorted(
        path
        for path in BOOKS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() != ".md"
    )


def find_book(book_name: str) -> Path:
    candidates = convertible_books()
    if not candidates:
        raise ValueError("No convertible book files found in books/.")

    query = normalize(book_name)
    exact = [
        path
        for path in candidates
        if query in {normalize(path.name), normalize(path.stem)}
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ValueError(
            "Multiple books matched exactly: "
            + ", ".join(path.name for path in exact)
        )

    partial = [
        path
        for path in candidates
        if query and query in normalize(path.name)
    ]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        raise ValueError(
            "Multiple books matched: " + ", ".join(path.name for path in partial)
        )

    raise ValueError(
        "No matching book found. Available books: "
        + ", ".join(path.name for path in candidates)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a book in books/ to Markdown via markitdown."
    )
    parser.add_argument(
        "book_name",
        help='Book name to match in books/ (example: "Think and Grow Rich")',
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output markdown path. Defaults to books/<book-stem>.md",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        source_path = find_book(args.book_name)
    except ValueError as exc:
        print(exc)
        sys.exit(1)

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source_path.with_suffix(".md")
    )

    if output_path.exists() and not args.force:
        print(f"Output already exists: {output_path}")
        print("Pass --force to overwrite, or use --output to choose another path.")
        sys.exit(1)

    try:
        from markitdown import MarkItDown
    except ModuleNotFoundError:
        print("markitdown is not installed in the current Python environment.")
        print("Run this via `make markitdown BOOK='...` after the project venv is set up.")
        sys.exit(1)

    print(f"Converting: {source_path.name}")
    result = MarkItDown().convert(str(source_path))
    output_path.write_text(result.text_content, encoding="utf-8")
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
