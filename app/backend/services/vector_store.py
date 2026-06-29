from __future__ import annotations

import json
import sqlite3
import struct
from pathlib import Path

import numpy as np


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            embedding BLOB,
            source TEXT,
            title TEXT,
            concept TEXT,
            emotions TEXT,
            lang TEXT,
            priority TEXT,
            book_refs TEXT
        )
        """
    )
    conn.commit()
    return conn


def pack_embedding(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def unpack_embedding(blob: bytes, dim: int) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32).copy()


def store_chunks(conn: sqlite3.Connection, chunks: list[dict], embeddings: np.ndarray) -> None:
    conn.execute("DELETE FROM chunks")
    for chunk, emb in zip(chunks, embeddings):
        conn.execute(
            """
            INSERT INTO chunks (id, text, embedding, source, title, concept, emotions, lang, priority, book_refs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk["id"],
                chunk["text"],
                pack_embedding(emb),
                chunk["source"],
                chunk["title"],
                chunk.get("concept", ""),
                json.dumps(chunk.get("emotions", [])),
                chunk.get("lang", "en"),
                chunk.get("priority", "medium"),
                json.dumps(chunk.get("book_refs", [])),
            ),
        )
    conn.commit()


def load_all_chunks(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, text, embedding, source, title, concept, emotions, lang, priority, book_refs FROM chunks"
    ).fetchall()
    results = []
    for row in rows:
        emb_blob = row[2]
        dim = len(emb_blob) // 4 if emb_blob else 0
        results.append(
            {
                "id": row[0],
                "text": row[1],
                "embedding": unpack_embedding(emb_blob, dim) if emb_blob else None,
                "source": row[3],
                "title": row[4],
                "concept": row[5],
                "emotions": json.loads(row[6] or "[]"),
                "lang": row[7],
                "priority": row[8],
                "book_refs": json.loads(row[9] or "[]"),
            }
        )
    return results
