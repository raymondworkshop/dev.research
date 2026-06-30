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
LOCAL_EMBED_DIR = DATABASE_PATH / "models" / "embeddings"

PROMPTS_DIR = ROOT / "prompts"
WIKI_DIR = ROOT / "wiki"
BOOKS_DIR = ROOT / "books"
RAW_DIR = ROOT / "raw"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

# LLM_PROVIDER: template | openai_compat | gemini
#   template       — emotion templates only (no model call)
#   openai_compat  — any OpenAI-compatible API (local MLX server, Ollama, OpenAI, …)
#   gemini         — Google Gemini via OpenAI-compatible endpoint
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "template").strip().lower()

LLM_API_BASE = os.getenv("LLM_API_BASE", os.getenv("MLX_API_BASE", "")).strip().rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("MLX_MODEL", "")).strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", LLM_API_KEY).strip()

GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"


def llm_enabled() -> bool:
    if LLM_PROVIDER == "template":
        return False
    if LLM_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY and LLM_MODEL)
    if LLM_PROVIDER in ("openai_compat", "mlx", "openai"):
        return bool(LLM_API_BASE and LLM_MODEL)
    return False


def llm_status_label() -> str:
    labels = {
        "template": "模板",
        "openai_compat": "LLM",
        "mlx": "MLX",
        "openai": "OpenAI",
        "gemini": "Gemini",
    }
    return labels.get(LLM_PROVIDER, LLM_PROVIDER)

SOURCE_BOOST = {
    "wiki": 1.0,
    "daily_stoic": 1.0,
    "meditations": 0.88,
    "raw_summary": 0.55,
}
