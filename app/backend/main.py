import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env.development")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import LLM_PROVIDER
from routes.chat import invalidate_cache, router as chat_router
from services.embedder import preload_embedder
from services.llm_provider import preload_mlx


@asynccontextmanager
async def lifespan(app: FastAPI):
    if LLM_PROVIDER == "mlx":
        import asyncio

        async def warm():
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, preload_embedder)
                await loop.run_in_executor(None, preload_mlx)
                print("Local models ready (embeddings + MLX).")
            except Exception as exc:
                print(f"Model preload failed: {exc}")

        asyncio.create_task(warm())
    yield


app = FastAPI(title="穩心 Steady Mind API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.post("/admin/reindex")
async def reindex():
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "scripts" / "ingest.py")], check=True)
    invalidate_cache()
    return {"status": "reindexed"}
