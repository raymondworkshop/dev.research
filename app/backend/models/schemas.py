from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., max_length=2000)
    lang: str = "auto"


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    chunk_count: int
    last_indexed_at: str | None
    model: str
