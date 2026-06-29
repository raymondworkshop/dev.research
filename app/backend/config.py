import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env.development")

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "./data"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = ROOT / DATABASE_PATH

VECTORS_DB = DATABASE_PATH / "vectors.db"
SESSIONS_DB = DATABASE_PATH / "sessions.db"
CHUNKS_JSON = DATABASE_PATH / "chunks.json"
LAST_INDEXED = DATABASE_PATH / "last_indexed_at"
LOCAL_MLX_DIR = DATABASE_PATH / "models" / "mlx"

PROMPTS_DIR = ROOT / "prompts"
WIKI_DIR = ROOT / "wiki"
BOOKS_DIR = ROOT / "books"
RAW_DIR = ROOT / "raw"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mlx")
LLM_MODEL = os.getenv("LLM_MODEL", "mlx-community/Qwen2.5-3B-Instruct-4bit")
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

SOURCE_BOOST = {
    "wiki": 1.0,
    "daily_stoic": 1.0,
    "meditations": 0.88,
    "raw_summary": 0.55,
}


def _is_mlx_model_dir(path: Path) -> bool:
    return path.is_dir() and (path / "config.json").exists()


def _latest_snapshot(cache_root: Path) -> Path | None:
    snapshots = cache_root / "snapshots"
    if not snapshots.is_dir():
        return None
    dirs = [p for p in snapshots.iterdir() if _is_mlx_model_dir(p)]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


def _hf_hub_cache_dir(model_id: str) -> Path:
    return Path.home() / ".cache" / "huggingface" / "hub" / f"models--{model_id.replace('/', '--')}"


def resolve_mlx_model_path() -> str:
    """
  Resolve a local directory for mlx_lm.load() — filesystem only, no HuggingFace API.
  Priority: LLM_MODEL_PATH → data/models/mlx → ~/.cache/huggingface/hub/...
    """
    if LLM_MODEL_PATH:
        path = Path(LLM_MODEL_PATH).expanduser()
        if not _is_mlx_model_dir(path):
            raise FileNotFoundError(f"LLM_MODEL_PATH invalid (need config.json): {path}")
        return str(path.resolve())

    if _is_mlx_model_dir(LOCAL_MLX_DIR):
        return str(LOCAL_MLX_DIR.resolve())

    cached = _latest_snapshot(_hf_hub_cache_dir(LLM_MODEL))
    if cached:
        return str(cached.resolve())

    raise FileNotFoundError(
        f"No local MLX model found for {LLM_MODEL}. "
        f"Run: make mlx-download  OR set LLM_MODEL_PATH to a snapshot directory."
    )
