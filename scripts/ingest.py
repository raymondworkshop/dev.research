from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from config import BOOKS_DIR, CHUNKS_JSON, DATABASE_PATH, LAST_INDEXED, RAW_DIR, VECTORS_DB, WIKI_DIR
from services.embedder import encode_passages, get_embedder
from services.vector_store import init_db, store_chunks
from chunkers.daily_stoic import chunk_daily_stoic
from chunkers.meditations import chunk_meditations
from chunkers.raw import chunk_raw
from chunkers.wiki import chunk_wiki
from tagger import tag_chunk


def collect_chunks() -> list[dict]:
    all_chunks = []
    print("Chunking books/TheDailyStoic...")
    ds = chunk_daily_stoic(BOOKS_DIR / "TheDailyStoic366Meditations.md")
    print(f"  {len(ds)} chunks")
    all_chunks.extend(ds)

    print("Chunking books/沉思录.md...")
    med = chunk_meditations(BOOKS_DIR / "沉思录.md")
    print(f"  {len(med)} chunks")
    all_chunks.extend(med)

    print("Chunking wiki/...")
    wiki = chunk_wiki(WIKI_DIR)
    print(f"  {len(wiki)} chunks")
    all_chunks.extend(wiki)

    print("Chunking raw/ (4 files)...")
    raw = chunk_raw(RAW_DIR)
    print(f"  {len(raw)} chunks")
    all_chunks.extend(raw)

    result = []
    for c in all_chunks:
        d = c.to_dict()
        fname = c.concept if c.source == "wiki" else ""
        d["emotions"] = tag_chunk(c.text, c.concept, fname)
        result.append(d)
    return result


def main() -> None:
    chunks = collect_chunks()
    if not chunks:
        print("No chunks found.")
        sys.exit(1)

    get_embedder()
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = encode_passages(texts, show_progress_bar=True)

    DATABASE_PATH.mkdir(parents=True, exist_ok=True)
    conn = init_db(VECTORS_DB)
    store_chunks(conn, chunks, embeddings)
    conn.close()

    CHUNKS_JSON.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    LAST_INDEXED.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    print(f"Wrote {VECTORS_DB} ({len(chunks)} chunks)")
    print("Restart backend (make dev) to load the new index.")


if __name__ == "__main__":
    main()
