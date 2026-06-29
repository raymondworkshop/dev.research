#!/usr/bin/env python3
"""Download embedding model to data/models/embeddings/ for offline RAG."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from config import EMBEDDING_MODEL
from services.embedder import EMBED_MODEL_MARKER, LOCAL_EMBED_DIR, _hf_cache_dir, _latest_snapshot


def main() -> None:
    force = "--force" in sys.argv

    if LOCAL_EMBED_DIR.is_dir() and not force:
        if EMBED_MODEL_MARKER.exists():
            current = EMBED_MODEL_MARKER.read_text(encoding="utf-8").strip()
            if current == EMBEDDING_MODEL:
                print(f"Already exists: {LOCAL_EMBED_DIR} ({current})")
                return
            print(f"Model changed ({current} -> {EMBEDDING_MODEL}), re-downloading...")
        else:
            print(f"Replacing legacy embeddings dir with {EMBEDDING_MODEL}...")
        shutil.rmtree(LOCAL_EMBED_DIR)

    cached = _latest_snapshot(_hf_cache_dir(EMBEDDING_MODEL))
    if cached and not force:
        LOCAL_EMBED_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(cached, LOCAL_EMBED_DIR)
        _prune_embedding_extras(LOCAL_EMBED_DIR)
        EMBED_MODEL_MARKER.write_text(EMBEDDING_MODEL, encoding="utf-8")
        print(f"Copied to {LOCAL_EMBED_DIR}")
        return

    if LOCAL_EMBED_DIR.is_dir():
        shutil.rmtree(LOCAL_EMBED_DIR)

    print(f"Downloading {EMBEDDING_MODEL} ...")
    from huggingface_hub import snapshot_download

    LOCAL_EMBED_DIR.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        EMBEDDING_MODEL,
        local_dir=str(LOCAL_EMBED_DIR),
        ignore_patterns=["onnx/*", "openvino/*", "pytorch_model.bin"],
    )
    _prune_embedding_extras(LOCAL_EMBED_DIR)
    EMBED_MODEL_MARKER.write_text(EMBEDDING_MODEL, encoding="utf-8")
    print(f"Done: {LOCAL_EMBED_DIR}")


def _prune_embedding_extras(path: Path) -> None:
    """Remove formats not used by sentence-transformers (saves ~1.5GB)."""
    for name in ("onnx", "openvino"):
        extra = path / name
        if extra.is_dir():
            shutil.rmtree(extra)
    bin_file = path / "pytorch_model.bin"
    if bin_file.is_file():
        bin_file.unlink()


if __name__ == "__main__":
    main()
