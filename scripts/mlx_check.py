#!/usr/bin/env python3
"""Verify MLX local model can load and generate."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend"))

from config import LLM_MODEL, resolve_mlx_model_path


def main() -> None:
    import mlx.core as mx
    from mlx_lm import generate, load

    print(f"MLX device: {mx.default_device()}")
    path = resolve_mlx_model_path()
    print(f"Local path: {path}")
    print("Loading...")
    model, tokenizer = load(path)
    print("Loaded.")

    messages = [
        {"role": "system", "content": "Reply in one Traditional Chinese sentence."},
        {"role": "user", "content": "穩心是什么？"},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    out = generate(model, tokenizer, prompt=prompt, max_tokens=60, verbose=False)
    print(f"Sample: {out.strip()}")
    print("OK — MLX ready.")


if __name__ == "__main__":
    main()
