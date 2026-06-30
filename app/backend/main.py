import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from routes.chat import invalidate_cache, router as chat_router
from services.embedder import preload_embedder


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, preload_embedder)
        print("Embeddings ready.")
    except Exception as exc:
        print(f"Embedder preload failed: {exc}")
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

    env = {**os.environ, "PYTHONPATH": f"{BACKEND}:{ROOT / 'scripts'}"}
    subprocess.run([sys.executable, str(ROOT / "scripts" / "ingest.py")], cwd=ROOT, env=env, check=True)
    invalidate_cache()
    return {"status": "reindexed"}
