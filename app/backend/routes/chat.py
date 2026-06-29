from __future__ import annotations

import asyncio
import json

import numpy as np
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from config import LAST_INDEXED, LLM_MODEL, LLM_PROVIDER, VECTORS_DB, resolve_mlx_model_path
from models.schemas import ChatRequest
from services.embedder import encode_query, get_embedder, resolve_embedding_path
from services.llm_provider import get_llm_provider
from services.prompt import build_messages, compose_structured_reply, rag_fallback_reply
from services.lang_detect import resolve_reply_lang
from services.quality import is_low_quality
from services.retriever import hybrid_search
from services.router import route_message
from services.safety import check_crisis, crisis_response
from services.session import get_history, save_turn
from services.vector_store import init_db, load_all_chunks

router = APIRouter()

_chunks_cache: list[dict] | None = None


def get_chunks() -> list[dict]:
    global _chunks_cache
    if _chunks_cache is None:
        if not VECTORS_DB.exists():
            return []
        conn = init_db(VECTORS_DB)
        _chunks_cache = load_all_chunks(conn)
        conn.close()
    return _chunks_cache


def _retrieve(message: str, emotion: str) -> tuple[list[dict], bool]:
    query_emb = encode_query(message)
    return hybrid_search(get_chunks(), query_emb, emotion_route=emotion)


def invalidate_cache():
    global _chunks_cache
    _chunks_cache = None


@router.post("/chat")
async def chat(req: ChatRequest):
    async def event_generator():
        lang = resolve_reply_lang(req.lang, req.message)

        if check_crisis(req.message):
            text = crisis_response(lang)
            yield {"event": "crisis", "data": json.dumps({"message": text})}
            yield {"event": "done", "data": "{}"}
            return

        emotion, mode = route_message(req.message)
        yield {"event": "status", "data": json.dumps({"message": "檢索相關文獻中…"})}
        await asyncio.sleep(0)

        chunks = get_chunks()
        if not chunks:
            yield {
                "event": "token",
                "data": json.dumps({"text": "知識庫尚未建立。請先執行 make ingest。"}),
            }
            yield {"event": "done", "data": "{}"}
            return

        yield {"event": "status", "data": json.dumps({"message": "比對 wiki 與書籍段落…"})}
        await asyncio.sleep(0)

        loop = asyncio.get_event_loop()
        top_chunks, weak = await loop.run_in_executor(
            None, lambda: _retrieve(req.message, emotion)
        )

        for c in top_chunks:
            yield {
                "event": "citation",
                "data": json.dumps({"id": c["id"], "title": c["title"], "source": c["source"], "score": round(c["score"], 3)}),
            }

        yield {"event": "status", "data": json.dumps({"message": "穩心整理回覆中…"})}

        history = get_history(req.session_id)
        messages = build_messages(
            req.message, top_chunks, history, lang=lang, mode=mode, weak_context=weak, emotion=emotion
        )

        save_turn(req.session_id, "user", req.message)
        llm = get_llm_provider()

        # feel mode: deterministic templates (zh + en)
        if lang in ("zh-Hant", "zh-Hans", "en") and mode == "feel":
            full_reply = compose_structured_reply(
                req.message, top_chunks, lang=lang, mode=mode, emotion=emotion
            )
        else:
            full_reply = ""
            try:
                yield {"event": "status", "data": json.dumps({"message": "穩心思考中（本地 MLX）…"})}
                full_reply = await llm.generate_full(messages)
                if is_low_quality(full_reply):
                    full_reply = rag_fallback_reply(
                        req.message, top_chunks, lang=lang, mode=mode, emotion=emotion
                    )
            except Exception as exc:
                full_reply = rag_fallback_reply(
                    req.message, top_chunks, lang=lang, mode=mode, emotion=emotion
                )
                full_reply += f"\n\n（MLX 回覆暫不可用：{exc}）"

        for i in range(0, len(full_reply), 8):
            chunk = full_reply[i : i + 8]
            yield {"event": "token", "data": json.dumps({"text": chunk})}
            await asyncio.sleep(0)

        save_turn(req.session_id, "assistant", full_reply)
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())


@router.get("/health")
async def health():
    chunks = get_chunks()
    last_indexed = None
    if LAST_INDEXED.exists():
        last_indexed = LAST_INDEXED.read_text(encoding="utf-8").strip()
    model_path = None
    if LLM_PROVIDER == "mlx":
        try:
            model_path = resolve_mlx_model_path()
        except Exception:
            model_path = None
    provider = get_llm_provider()
    mlx_loaded = getattr(provider, "_model", None) is not None
    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "chunk_count": len(chunks),
        "last_indexed_at": last_indexed,
        "model": LLM_MODEL,
        "model_path": model_path,
        "embedding_path": resolve_embedding_path(),
        "mlx_loaded": mlx_loaded,
    }
