from __future__ import annotations

import re
from collections import Counter


def control_labels_invalid(text: str) -> bool:
    """True when 可控/不可控 labels are missing or swapped."""
    if "**可控**" not in text or "**不可控**" not in text:
        return True

    ctrl_match = re.search(r"\*\*可控\*\*[：:]\s*(.+?)(?=\n\*\*不可控\*\*|\n斯多葛|\n摘錄|\n今天|$)", text, re.DOTALL)
    not_match = re.search(r"\*\*不可控\*\*[：:]\s*(.+?)(?=\n\*\*可控\*\*|\n斯多葛|\n摘錄|\n今天|$)", text, re.DOTALL)
    if not ctrl_match or not not_match:
        return True

    ctrl = ctrl_match.group(1)
    deny_markers = (
        "不在你", "不在你的", "無法", "无法", "無法改變", "无法改变",
        "她的決定", "她的决定", "他的決定", "他的决定", "不是你能", "你無法", "你无法",
    )
    return any(m in ctrl for m in deny_markers)


def is_low_quality(text: str) -> bool:
    """Detect garbled MLX output, runaway repetition, or bad control labels."""
    if control_labels_invalid(text):
        return True
    stripped = text.strip()
    if len(stripped) < 40:
        return True

    garble_markers = (
        r"\[[dk][a-z]{3,}",
        r"kiation",
        r"topations",
        r"notiseduture",
        r"rators",
    )
    for pattern in garble_markers:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    sentences = [s.strip() for s in re.split(r"[。！？\n]+", stripped) if len(s.strip()) > 14]
    if sentences:
        _, count = Counter(sentences).most_common(1)[0]
        if count >= 3:
            return True

    return False
