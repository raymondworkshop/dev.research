from __future__ import annotations

import re

EMOTION_KEYWORDS: dict[str, list[str]] = {
    "anger": [
        "anger", "angry", "rage", "furious", "憤怒", "暴怒", "生气", "氣", "恼火",
    ],
    "grief": [
        "grief", "grieve", "loss", "mourning", "悲痛", "悲伤", "悲傷", "去世", "失去",
    ],
    "insult": [
        "insult", "offend", "humiliat", "羞辱", "侮辱", "冒犯", "被骂", "被罵",
    ],
    "reputation": [
        "reputation", "opinion", "judgment", "judgement", "名声", "名聲", "评价", "評價",
    ],
    "control": [
        "control", "controllable", "dichotomy", "可控", "控制", "二分", "无奈", "無奈", "郁闷", "鬱悶",
    ],
    "social_conflict": [
        "conflict", "relationship", "social", "人际", "人際", "交往", "冲突", "衝突",
        "追求", "女生", "传话", "傳話", "中间人", "中間人",
        "girl", "boy", "guy", "crush", "dating", "love", "loving", "pursuing", "pursue",
        "communicate", "communication", "text back", "reply", "ghost", "ghosting",
        "intermediary", "middleman", "mutual friend", "third party",
        "tired", "exhausted", "drained",
    ],
    "present_moment": [
        "present", "now", "moment", "当下", "當下", "活在", "现在", "現在",
    ],
    "negative_visualization": [
        "negative visualization", "premeditatio", "消極想像", "消极想象", "预想", "預想",
    ],
}

FILENAME_EMOTIONS: dict[str, list[str]] = {
    "handling-insults": ["insult"],
    "emotions": ["anger", "grief"],
    "dichotomy-of-control": ["control"],
    "reputation": ["reputation"],
    "negative-visualization": ["negative_visualization"],
    "living-in-the-present": ["present_moment"],
    "social-duty": ["social_conflict"],
    "stoicism": ["general"],
}


def tag_chunk(text: str, concept: str = "", filename: str = "") -> list[str]:
    tags: set[str] = set()
    if filename and filename in FILENAME_EMOTIONS:
        tags.update(FILENAME_EMOTIONS[filename])
    lower = text.lower()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in lower or kw in text:
                tags.add(emotion)
                break
    if concept and concept in EMOTION_KEYWORDS:
        tags.add(concept)
    return sorted(tags) if tags else ["general"]


def route_message(message: str) -> tuple[str, str]:
    """Return (emotion_route, mode). More specific routes are checked first."""
    lower = message.lower()
    decide_signals = ["should i", "what do i do", "怎么办", "怎麼辦", "该不该", "該不該", "decide", "选择", "選擇"]
    mode = "decide" if any(s in lower or s in message for s in decide_signals) else "feel"

    priority = [
        "social_conflict",
        "insult",
        "grief",
        "anger",
        "reputation",
        "control",
        "present_moment",
        "negative_visualization",
    ]
    for emotion in priority:
        for kw in EMOTION_KEYWORDS[emotion]:
            if kw.lower() in lower or kw in message:
                return emotion, mode
    return "general", mode
