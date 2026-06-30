from __future__ import annotations

from services.lang_detect import to_simplified


def _is_pursuit_indirect(message: str) -> bool:
    lower = message.lower()
    keywords = (
        "追求", "女生", "男生", "喜歡", "喜欢", "传话", "傳話",
        "中间人", "中間人", "第三者", "中介", "媒人",
        "girl", "boy", "guy", "crush", "dating", "love", "loving", "pursuing", "pursue",
        "communicate", "communication", "ghost", "intermediary", "middleman",
        "mutual friend", "third party", "text back",
    )
    return any(k in message or k in lower for k in keywords)


def _scenario_copy_en(emotion: str, message: str) -> dict[str, str]:
    if emotion == "social_conflict" and _is_pursuit_indirect(message):
        return {
            "ack": "Feeling tired and shut out when she won't communicate directly is understandable.",
            "not_control": "Whether she replies directly, how she distances herself, or uses others to pass messages.",
            "in_control": "Whether you express yourself clearly once, with dignity, and how long you keep investing.",
            "reframe": "You cannot command her response, but you can choose how you act without being dragged into endless guessing.",
            "action": 'Say once, politely: "If you are open to it, I would like to talk directly." Then stop pushing.',
            "question": "If direct contact never happens, what deadline would you give yourself?",
        }
    if emotion in ("social_conflict", "reputation"):
        return {
            "ack": "Feeling hurt or stuck in a relationship is worth taking seriously.",
            "not_control": "How others see you and how they choose to engage.",
            "in_control": "Your tone, your boundaries, and whether you keep investing here.",
            "reframe": "Reputation lives outside you; your character and actions live within.",
            "action": "Today: say what you mean once, in a way you can stand behind.",
            "question": "Apart from her reaction, who do you want to be in this?",
        }
    return {
        "ack": "I hear the frustration in what you shared.",
        "not_control": "Others' choices, timing, and how they see you.",
        "in_control": "Your goals, values, and the next small action you own today.",
        "reframe": "Put energy into internal aims; let outcomes follow as they may.",
        "action": "Do one small thing today that is fully within your control.",
        "question": "What is one step you can actually move forward right now?",
    }


def _scenario_copy(emotion: str, message: str, lang: str = "zh-Hant") -> dict[str, str]:
    if lang == "en":
        return _scenario_copy_en(emotion, message)
    if emotion == "social_conflict" and _is_pursuit_indirect(message):
        return {
            "ack": "一直要透過中間人傳話，感到鬱悶、像被擋在外面，這很自然。",
            "not_control": "她是否願意直接和你說話、用什麼方式回應你",
            "in_control": "你是否清楚、有分寸地表明意圖一次，以及如何解讀沉默、是否繼續投入",
            "reframe": "你無法命令別人怎麼回應，但可以決定自己如何行動，而不被猜測拖垮。",
            "action": "禮貌說一次：「若方便，我想直接和你聊幾句。」說完即可，不反覆追問。",
            "question": "若始終沒有直接互動，你願意給自己一個等待的期限嗎？",
        }
    if emotion in ("social_conflict", "reputation"):
        return {
            "ack": "在人際裡感到委屈或無奈，這種感受值得被正視。",
            "not_control": "他人如何看待你、選擇怎麼與你相處",
            "in_control": "你是否維持分寸與善意、是否繼續投入這段關係",
            "reframe": "名聲與回應方式在外部；你的品格與行動在內部。",
            "action": "今天只做一件小事：用你認可的語氣，把話說清楚一次。",
            "question": "撇開對方的反應，你想成為什麼樣的自己？",
        }
    if emotion == "insult":
        return {
            "ack": "被冒犯時感到憤怒或難堪，都很正常。",
            "not_control": "別人說了什麼、懷著什麼動機",
            "in_control": "你如何判斷真假、是否回應、是否讓它佔據你一整天",
            "reframe": "若話屬實，就改進；若不實，那是對方的誤解，不必用情緒買單。",
            "action": "今天把注意力放回一件對你有價值的事上。",
            "question": "若這句話一年後無人記得，你還想讓它困住你嗎？",
        }
    if emotion == "grief":
        return {
            "ack": "失去與哀傷需要時間，不必催促自己立刻好起來。",
            "not_control": "已經發生的事、別人的離去或改變",
            "in_control": "你如何紀念、如何照顧自己、如何一步步恢復日常",
            "reframe": "悲痛不是敵人；理性要削減的是過分且不必要的部分。",
            "action": "今天做一件小事：好好吃一餐、寫下一段你想記住的事。",
            "question": "若對方仍在，你會希望被怎樣記得？",
        }
    if emotion == "anger":
        return {
            "ack": "怒火升起時，身體往往比頭腦更快。",
            "not_control": "別人做了什麼、世事如何變化",
            "in_control": "你如何詮釋、是否回擊、是否把今天交給憤怒",
            "reframe": "生命太短，不值得把心力耗在可忽略的刺激上。",
            "action": "先慢三次呼吸，再決定要不要回應。",
            "question": "十年後回看，這件事還值得你今天如此激動嗎？",
        }
    return {
        "ack": "聽見你的無奈，這種感受很自然。",
        "not_control": "他人的選擇、結果何時到來、別人怎麼看你",
        "in_control": "你的目標、價值觀、今天具體的行動與態度",
        "reframe": "把力氣用在內在目標上，外在結果順其自然。",
        "action": "今天只做一件你能完全負責的小事。",
        "question": "此刻，什麼是你真正能向前推進的一步？",
    }


def _maybe_simplify(text: str, lang: str) -> str:
    if lang == "zh-Hans":
        return to_simplified(text)
    return text


def compose_reply(
    user_message: str,
    *,
    lang: str = "zh-Hant",
    mode: str = "feel",
    emotion: str = "general",
    weak_context: bool = False,
) -> str:
    """Template reply from emotion routing and stoic framing."""
    if lang == "en":
        if mode == "decide":
            body = (
                "Let's sort the situation:\n\n"
                "**In your control**: Your actions, attitude, and choices.\n"
                "**Not in your control**: Others' reactions and final outcomes.\n\n"
                "If you could only do one thing, which would you pick?"
            )
            if weak_context:
                body += "\n\n(I couldn't find a strong passage — this is general Stoic framing.)"
            return body
        copy = _scenario_copy(emotion, user_message, lang="en")
        body = (
            f"Acknowledge: {copy['ack']}\n\n"
            f"Not in your control: {copy['not_control']}\n"
            f"In your control: {copy['in_control']}\n\n"
            f"Stoic reframe: {copy['reframe']}\n\n"
            f"One small step today: {copy['action']}\n\n"
            f"{copy['question']}"
        )
        if weak_context:
            body += "\n\n(I couldn't find a strong passage — this is general Stoic framing.)"
        return body

    if mode == "decide":
        body = (
            "先把處境整理如下：\n\n"
            "可控：你的行動、態度與選擇。\n\n"
            "不可控：他人的反應與最終結果。\n\n"
            "若只能做一件事，你會選哪一個？"
        )
        if weak_context:
            body += "\n\n（未找到強相關段落，以下為一般斯多葛框架。）"
        return _maybe_simplify(body, lang)

    copy = _scenario_copy(emotion, user_message, lang="zh-Hant")
    body = (
        f"承認情緒：{copy['ack']}\n\n"
        f"不可控：{copy['not_control']}\n"
        f"可控：{copy['in_control']}\n\n"
        f"斯多葛重述：{copy['reframe']}\n\n"
        f"今天可做的一件小事：{copy['action']}\n\n"
        f"{copy['question']}"
    )
    if weak_context:
        body += "\n\n（未找到強相關段落，以下為一般斯多葛框架。）"
    return _maybe_simplify(body, lang)


def load_stoic_guide() -> str:
    from config import PROMPTS_DIR

    return (PROMPTS_DIR / "stoic_guide.md").read_text(encoding="utf-8")


def build_messages(
    user_message: str,
    chunks: list[dict],
    history: list[dict],
    *,
    lang: str = "zh-Hant",
    mode: str = "feel",
    weak_context: bool = False,
    emotion: str = "general",
) -> list[dict]:
    system = load_stoic_guide()
    lang_instruction = {
        "zh-Hant": "Respond in Traditional Chinese (繁體中文).",
        "zh-Hans": "Respond in Simplified Chinese (简体中文).",
        "en": "Respond in English.",
    }.get(lang, "Match the user's language.")

    context_parts = []
    for c in chunks[:4]:
        cite_id = c.get("title", c["id"])
        context_parts.append(f"[{cite_id}]\n{c['text'][:400]}")

    context_block = "\n\n---\n\n".join(context_parts) if context_parts else "(no context)"
    weak_note = (
        "\n\nNote: retrieval confidence is low. Say you lack a strong passage and offer general Stoic framing."
        if weak_context
        else ""
    )

    format_hint = ""
    if mode == "feel" and lang in ("zh-Hant", "zh-Hans"):
        format_hint = """
回覆格式（必須嚴格遵守，不可調換順序）：
1. 承認情緒：（1–2 句，先寫感受）
2. **不可控**：（他人/結果/對方行為；禁止寫「你可以…」）
3. **可控**：（自己的行動/態度/選擇）
4. 斯多葛重述：（1 句）
5. 今天可做的一件小事：（1 句，具體、有分寸）
6. 結尾一個問題

禁止：重複小標題、戀愛攻略式建議、在未承認情緒前寫不可控/可控。
追求/傳話情境：可控=有尊嚴地表明意圖一次；不可催促表白或反覆追問。
"""

    system_content = f"""{system}

Mode: **{mode}** | Route: **{emotion}**
{lang_instruction}
{format_hint}
Cite sources using [title] from the context below.{weak_note}

## Retrieved context
{context_block}
"""

    messages: list[dict] = [{"role": "system", "content": system_content}]
    for turn in history[-4:]:
        if turn["role"] in ("user", "assistant"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages
