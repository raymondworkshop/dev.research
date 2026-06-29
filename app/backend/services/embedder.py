from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from config import EMBEDDING_MODEL, ROOT

LOCAL_EMBED_DIR = ROOT / "data" / "models" / "embeddings"
EMBED_MODEL_MARKER = LOCAL_EMBED_DIR / ".embedding_model"

_embedder = None


def _hf_cache_dir(model_id: str) -> Path:
    return Path.home() / ".cache" / "huggingface" / "hub" / f"models--{model_id.replace('/', '--')}"


def _latest_snapshot(cache_root: Path) -> Path | None:
    snaps = cache_root / "snapshots"
    if not snaps.is_dir():
        return None
    dirs = [p for p in snaps.iterdir() if p.is_dir()]
    return max(dirs, key=lambda p: p.stat().st_mtime) if dirs else None


def is_e5_model(model_id: str | None = None) -> bool:
    name = (model_id or EMBEDDING_MODEL).lower()
    return "e5" in name and "multilingual" in name


def resolve_embedding_path() -> str | None:
    """Local embedding model directory, or None to use model id."""
    if LOCAL_EMBED_DIR.is_dir():
        if EMBED_MODEL_MARKER.exists():
            if EMBED_MODEL_MARKER.read_text(encoding="utf-8").strip() != EMBEDDING_MODEL:
                return None
        return str(LOCAL_EMBED_DIR)
    cached = _latest_snapshot(_hf_cache_dir(EMBEDDING_MODEL))
    return str(cached) if cached else None


def create_sentence_transformer(model_ref: str | None = None, device: str | None = None):
    import torch
    from sentence_transformers import SentenceTransformer

    if device is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"

    local = resolve_embedding_path()
    if model_ref is None:
        if local:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            print(f"Loading embeddings from local: {local}")
            model_ref = local
        else:
            print(f"Loading embeddings: {EMBEDDING_MODEL} (will cache locally)")
            model_ref = EMBEDDING_MODEL

    return SentenceTransformer(model_ref, device=device)


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = create_sentence_transformer()
    return _embedder


def encode_query(text: str) -> np.ndarray:
    model = get_embedder()
    prompt = f"query: {text}" if is_e5_model() else text
    return np.array(model.encode(prompt, normalize_embeddings=True))


def encode_passages(texts: list[str], show_progress_bar: bool = False) -> np.ndarray:
    model = get_embedder()
    if is_e5_model():
        texts = [f"passage: {t}" for t in texts]
    return np.array(
        model.encode(texts, normalize_embeddings=True, show_progress_bar=show_progress_bar)
    )


def preload_embedder() -> None:
    get_embedder()
