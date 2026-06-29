from __future__ import annotations

CRISIS_KEYWORDS = [
    "自杀", "自殺", "想死", "不想活", "了结", "了結", "结束生命", "結束生命",
    "suicide", "kill myself", "end my life", "self-harm", "self harm",
    "hurt myself", "want to die",
]

HOTLINES = {
    "zh-Hant": [
        "台灣 1925 安心專線",
        "生命線 1995",
        "張老師 1980",
    ],
    "zh-Hans": [
        "北京心理危机研究与干预中心 010-82951332",
        "全国心理援助热线 12356",
    ],
    "en": [
        "988 Suicide & Crisis Lifeline (US)",
        "Samaritans 116 123 (UK)",
    ],
}


def check_crisis(message: str) -> bool:
    lower = message.lower()
    return any(kw in message or kw in lower for kw in CRISIS_KEYWORDS)


def crisis_response(lang: str = "zh-Hant") -> str:
    lines = HOTLINES.get(lang, HOTLINES["zh-Hant"])
    header = {
        "zh-Hant": "若你正在經歷嚴重痛苦，請聯繫專業協助：",
        "zh-Hans": "若你正在经历严重痛苦，请联系专业协助：",
        "en": "If you are in crisis, please contact professional support:",
    }.get(lang, HOTLINES["zh-Hant"][0])
    body = "\n".join(f"· {line}" for line in lines)
    footer = {
        "zh-Hant": "本工具無法提供危機支援。",
        "zh-Hans": "本工具无法提供危机支援。",
        "en": "This tool cannot provide crisis support.",
    }.get(lang, "")
    return f"{header}\n{body}\n\n{footer}"
