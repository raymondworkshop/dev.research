#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "backend"))

from config import VECTORS_DB
from services.embedder import encode_query, get_embedder
from services.retriever import hybrid_search
from services.router import route_message
from services.vector_store import init_db, load_all_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", default="")
    parser.add_argument("--msg", dest="msg", default="")
    args = parser.parse_args()
    message = args.msg or args.message or "同事当众羞辱我"
    if not VECTORS_DB.exists():
        print(f"Run make ingest first. ({VECTORS_DB} not found)")
        sys.exit(1)

    get_embedder()
    emotion, mode = route_message(message)
    print(f"Route: {emotion} | mode: {mode}\n")
    query_emb = encode_query(message)
    conn = init_db(VECTORS_DB)
    chunks = load_all_chunks(conn)
    conn.close()
    top, weak = hybrid_search(chunks, query_emb, emotion_route=emotion)
    if weak:
        print("(low confidence retrieval)\n")
    for i, c in enumerate(top, 1):
        print(f"#{i}  score={c['score']:.3f}  {c['title']}")
        print(f"    source={c['source']}  emotions={c.get('emotions')}")
        print()


if __name__ == "__main__":
    main()
