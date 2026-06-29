from __future__ import annotations

import numpy as np

from config import SOURCE_BOOST


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def hybrid_search(
    chunks: list[dict],
    query_embedding: np.ndarray,
    emotion_route: str = "general",
    top_k: int = 6,
    min_score: float = 0.35,
) -> tuple[list[dict], bool]:
    scored = []
    for chunk in chunks:
        emb = chunk.get("embedding")
        if emb is None:
            continue
        sim = cosine_sim(query_embedding, emb)
        source_boost = SOURCE_BOOST.get(chunk["source"], 0.5)
        emotions = chunk.get("emotions", [])
        concept_match = 1.0 if emotion_route in emotions else 0.0
        if emotion_route == "general" and "general" in emotions:
            concept_match = 0.5
        final = 0.5 * sim + 0.3 * concept_match + 0.2 * source_boost
        scored.append({**chunk, "score": final, "sim": sim})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_k]
    weak = not top or top[0]["score"] < min_score
    return top, weak
