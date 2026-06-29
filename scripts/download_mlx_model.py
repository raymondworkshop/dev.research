#!/usr/bin/env python3
"""Download MLX model once into data/models/mlx/ for fully offline use."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from config import LLM_MODEL, LOCAL_MLX_DIR, resolve_mlx_model_path


def main() -> None:
    try:
        existing = resolve_mlx_model_path()
        print(f"Local MLX already available: {existing}")
        if not _has_config(LOCAL_MLX_DIR) and _has_config(Path(existing)):
            LOCAL_MLX_DIR.parent.mkdir(parents=True, exist_ok=True)
            if LOCAL_MLX_DIR.exists():
                shutil.rmtree(LOCAL_MLX_DIR)
            shutil.copytree(existing, LOCAL_MLX_DIR)
            print(f"Copied to project: {LOCAL_MLX_DIR}")
        return
    except FileNotFoundError:
        pass

    print(f"Downloading {LLM_MODEL} to {LOCAL_MLX_DIR} ...")
    LOCAL_MLX_DIR.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_MLX_DIR.exists():
        shutil.rmtree(LOCAL_MLX_DIR)

    from huggingface_hub import snapshot_download

    path = snapshot_download(LLM_MODEL, local_dir=str(LOCAL_MLX_DIR))
    print(f"Done: {path}")
    print("Set LLM_MODEL_PATH optional; data/models/mlx is used automatically.")


def _has_config(p: Path) -> bool:
    return p.is_dir() and (p / "config.json").exists()


if __name__ == "__main__":
    main()
