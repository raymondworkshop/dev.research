from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Protocol

from config import LLM_PROVIDER, resolve_mlx_model_path


class LLMProvider(Protocol):
    async def stream_chat(self, messages: list[dict]) -> AsyncIterator[str]: ...


class MLXProvider:
    """mlx_lm.load(local_dir) + stream_generate — Apple Silicon, no cloud."""

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._load_error: str | None = None
        self.model_path: str | None = None

    def _load(self):
        if self._load_error:
            raise RuntimeError(self._load_error)
        if self._model is not None:
            return

        from mlx_lm import load

        self.model_path = resolve_mlx_model_path()
        print(f"Loading MLX from local path: {self.model_path}")
        try:
            self._model, self._tokenizer = load(self.model_path)
        except Exception as exc:
            self._load_error = str(exc)
            raise RuntimeError(f"無法載入本地 MLX 模型：{exc}") from exc

    async def stream_chat(self, messages: list[dict]) -> AsyncIterator[str]:
        text = await self.generate_full(messages)
        for i in range(0, len(text), 8):
            yield text[i : i + 8]

    async def generate_full(self, messages: list[dict]) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._generate_full_sync(messages))

    def _generate_full_sync(self, messages: list[dict]) -> str:
        self._load()

        from mlx_lm import stream_generate

        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        parts: list[str] = []
        for response in stream_generate(
            self._model,
            self._tokenizer,
            prompt,
            max_tokens=320,
        ):
            text = response.text if hasattr(response, "text") else str(response)
            if text:
                parts.append(text)
        return "".join(parts)


class GeminiProvider:
    """Stage B — cloud only."""

    async def stream_chat(self, messages: list[dict]) -> AsyncIterator[str]:
        yield "Gemini provider not configured. Set LLM_PROVIDER=mlx for local dev."
        if False:
            yield ""


_mlx_singleton: MLXProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _mlx_singleton
    if LLM_PROVIDER == "gemini":
        return GeminiProvider()
    if _mlx_singleton is None:
        _mlx_singleton = MLXProvider()
    return _mlx_singleton


def preload_mlx() -> None:
    """Load local MLX weights into memory (call once at startup)."""
    if LLM_PROVIDER == "mlx":
        get_llm_provider()._load()
