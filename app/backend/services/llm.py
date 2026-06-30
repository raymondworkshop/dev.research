from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Protocol

import httpx

from config import (
    GEMINI_API_KEY,
    GEMINI_OPENAI_BASE,
    LLM_API_BASE,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    llm_enabled,
)


class LLMProvider(Protocol):
    name: str
    model: str

    async def stream_chat(self, messages: list[dict], *, max_tokens: int = 320) -> AsyncIterator[str]: ...

    async def check_health(self) -> bool: ...


class OpenAICompatProvider:
    """OpenAI-compatible chat/completions (local MLX, Ollama, OpenAI, Gemini compat, …)."""

    name = "openai_compat"

    def __init__(self, *, base_url: str, model: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def stream_chat(self, messages: list[dict], *, max_tokens: int = 320) -> AsyncIterator[str]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": True,
        }
        timeout = httpx.Timeout(120.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload, headers=self._headers()) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if not data or data == "[DONE]":
                        continue
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    text = delta.get("content")
                    if text:
                        yield text

    async def check_health(self) -> bool:
        try:
            timeout = httpx.Timeout(5.0, connect=3.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
                return resp.is_success
        except Exception:
            return False


class GeminiProvider(OpenAICompatProvider):
    """Gemini via Google's OpenAI-compatible endpoint."""

    name = "gemini"

    def __init__(self, *, model: str, api_key: str):
        super().__init__(base_url=GEMINI_OPENAI_BASE, model=model, api_key=api_key)


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider | None:
    global _provider
    if not llm_enabled():
        return None
    if _provider is None:
        _provider = _build_provider()
    return _provider


def _build_provider() -> LLMProvider:
    if LLM_PROVIDER == "gemini":
        return GeminiProvider(model=LLM_MODEL, api_key=GEMINI_API_KEY)
    if LLM_PROVIDER in ("openai_compat", "mlx", "openai"):
        return OpenAICompatProvider(
            base_url=LLM_API_BASE,
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


async def check_llm_health() -> bool:
    provider = get_llm_provider()
    if provider is None:
        return False
    return await provider.check_health()
