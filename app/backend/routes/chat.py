from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from config import EMBEDDING_MODEL, LAST_INDEXED, LLM_MODEL, LLM_PROVIDER, VECTORS_DB, llm_enabled, llm_status_label
from models.schemas import ChatRequest
from services.embedder import encode_query, resolve_embedding_path
from services.lang_detect import resolve_reply_lang
from services.llm import check_llm_health, get_llm_provider
from services.prompt import build_messages, compose_reply
from services.quality import is_low_quality
from services.retriever import hybrid_search
from services.safety import check_crisis, crisis_response
from services.session import get_history, save_turn
from services.tagger import route_message
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


async def _emit_reply(full_reply: str):
    for i in range(0, len(full_reply), 8):
        chunk = full_reply[i : i + 8]
        yield {"event": "token", "data": json.dumps({"text": chunk})}
        await asyncio.sleep(0)


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

        save_turn(req.session_id, "user", req.message)
        full_reply = ""
        provider = get_llm_provider()

        # feel: curated templates (reliable format + stoic framing)
        # decide: LLM when configured, with quality fallback
        use_llm = provider is not None and mode == "decide"

        if use_llm:
            label = llm_status_label()
            yield {"event": "status", "data": json.dumps({"message": f"穩心思考中（{label}）…"})}
            history = get_history(req.session_id)
            if history and history[-1]["role"] == "user" and history[-1]["content"] == req.message:
                history = history[:-1]
            messages = build_messages(
                req.message,
                top_chunks,
                history,
                lang=lang,
                mode=mode,
                weak_context=weak,
                emotion=emotion,
            )
            try:
                async for token in provider.stream_chat(messages):
                    full_reply += token
                    yield {"event": "token", "data": json.dumps({"text": token})}
                if is_low_quality(full_reply, lang=lang, mode=mode, emotion=emotion):
                    yield {"event": "status", "data": json.dumps({"message": "改用模板回覆…"})}
                    full_reply = compose_reply(
                        req.message, lang=lang, mode=mode, emotion=emotion, weak_context=weak
                    )
                    async for event in _emit_reply(full_reply):
                        yield event
            except Exception as exc:
                if not full_reply:
                    yield {"event": "status", "data": json.dumps({"message": "模型暫不可用，改用模板回覆…"})}
                    full_reply = compose_reply(
                        req.message, lang=lang, mode=mode, emotion=emotion, weak_context=weak
                    )
                    full_reply += f"\n\n（{label} 回覆暫不可用：{exc}）"
                    async for event in _emit_reply(full_reply):
                        yield event
                else:
                    note = f"\n\n（{label} 回覆中斷：{exc}）"
                    full_reply += note
                    yield {"event": "token", "data": json.dumps({"text": note})}
        else:
            yield {"event": "status", "data": json.dumps({"message": "穩心整理回覆中…"})}
            full_reply = compose_reply(
                req.message, lang=lang, mode=mode, emotion=emotion, weak_context=weak
            )
            async for event in _emit_reply(full_reply):
                yield event

        save_turn(req.session_id, "assistant", full_reply)
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())


@router.get("/health")
async def health():
    chunks = get_chunks()
    last_indexed = None
    if LAST_INDEXED.exists():
        last_indexed = LAST_INDEXED.read_text(encoding="utf-8").strip()
    provider = get_llm_provider()
    return {
        "status": "ok",
        "chunk_count": len(chunks),
        "last_indexed_at": last_indexed,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_path": resolve_embedding_path(),
        "llm_provider": LLM_PROVIDER,
        "llm_model": LLM_MODEL if llm_enabled() else None,
        "llm_reachable": await check_llm_health() if provider else None,
    }
