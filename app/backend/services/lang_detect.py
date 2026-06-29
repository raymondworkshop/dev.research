from __future__ import annotations

import re
from functools import lru_cache


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def is_mostly_english(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if ord(c) < 128)
    return latin / len(letters) >= 0.75


@lru_cache(maxsize=1)
def _t2s():
    from opencc import OpenCC

    return OpenCC("t2s")


def detect_zh_variant(text: str) -> str:
    """Return zh-Hant or zh-Hans based on characters in the message."""
    if not has_cjk(text):
        return "zh-Hant"
    if _t2s().convert(text) != text:
        return "zh-Hant"
    return "zh-Hans"


def to_simplified(text: str) -> str:
    return _t2s().convert(text)


def resolve_reply_lang(requested: str, message: str) -> str:
    """
    Pick reply language from UI setting + user message.
    - auto: English message → en; Chinese → 简/繁
    - zh-Hant / zh-Hans / en: force that variant
    """
    if requested == "en":
        return "en"
    if requested == "zh-Hant":
        return "zh-Hant"
    if requested == "zh-Hans":
        return "zh-Hans"
    if is_mostly_english(message):
        return "en"
    if not has_cjk(message):
        return "zh-Hant"
    return detect_zh_variant(message)
