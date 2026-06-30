from __future__ import annotations

import re


def is_low_quality(
    text: str,
    *,
    lang: str = "zh-Hant",
    mode: str = "feel",
    emotion: str = "general",
) -> bool:
    """Detect garbled or off-format LLM output worth replacing with templates."""
    t = text.strip()
    if len(t) < 50:
        return True

    if lang in ("zh-Hant", "zh-Hans") and mode == "feel":
        ack_markers = ("承認情緒", "承認", "聽見你的")
        ack_idx = min((t.find(m) for m in ack_markers if m in t), default=-1)
        not_idx = t.find("不可控")
        if not_idx >= 0 and (ack_idx < 0 or not_idx < ack_idx):
            return True

        for marker in ("承認情緒", "今天可做的一件小事", "可控行動", "結尾一個問題"):
            if t.count(marker) > 1:
                return True

        if emotion == "social_conflict" and _is_pursuit_risk(t):
            return True

    if re.search(r"(.{{8,}})\1{2,}", t):
        return True

    return False


def _is_pursuit_risk(text: str) -> bool:
    """Reject pushy dating advice that violates stoic_guide."""
    risky = (
        "直接表達對她的感情",
        "表達對她的感情",
        "表達我的心意",
        "直接向她表白",
        "追求她",
        "讓她知道你的心意",
        "表白",
    )
    return any(p in text for p in risky)
