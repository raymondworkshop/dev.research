const TRAD_TO_SIMP: Record<string, string> = {
  "佔": "占",
  "來": "来",
  "係": "系",
  "個": "个",
  "們": "们",
  "傳": "传",
  "傷": "伤",
  "價": "价",
  "內": "内",
  "別": "别",
  "剛": "刚",
  "動": "动",
  "問": "问",
  "單": "单",
  "嗎": "吗",
  "嚴": "严",
  "國": "国",
  "妳": "你",
  "實": "实",
  "寫": "写",
  "專": "专",
  "對": "对",
  "屬": "属",
  "師": "师",
  "幾": "几",
  "張": "张",
  "強": "强",
  "後": "后",
  "復": "复",
  "悶": "闷",
  "憂": "忧",
  "憤": "愤",
  "應": "应",
  "懷": "怀",
  "擇": "择",
  "擊": "击",
  "擋": "挡",
  "擔": "担",
  "據": "据",
  "敵": "敌",
  "斷": "断",
  "時": "时",
  "書": "书",
  "會": "会",
  "東": "东",
  "標": "标",
  "樣": "样",
  "機": "机",
  "檢": "检",
  "歷": "历",
  "氣": "气",
  "決": "决",
  "沒": "没",
  "減": "减",
  "灣": "湾",
  "為": "为",
  "無": "无",
  "牠": "它",
  "當": "当",
  "眾": "众",
  "禮": "礼",
  "種": "种",
  "穩": "稳",
  "籍": "籍",
  "紀": "纪",
  "索": "索",
  "終": "终",
  "結": "结",
  "給": "给",
  "經": "经",
  "緒": "绪",
  "線": "线",
  "總": "总",
  "繫": "系",
  "繼": "继",
  "續": "续",
  "纔": "才",
  "聯": "联",
  "聲": "声",
  "聽": "听",
  "腦": "脑",
  "臺": "台",
  "與": "与",
  "萬": "万",
  "著": "着",
  "處": "处",
  "裏": "里",
  "裡": "里",
  "覆": "复",
  "見": "见",
  "視": "视",
  "親": "亲",
  "觀": "观",
  "訊": "讯",
  "記": "记",
  "評": "评",
  "詮": "诠",
  "話": "话",
  "認": "认",
  "語": "语",
  "誤": "误",
  "說": "说",
  "請": "请",
  "識": "识",
  "議": "议",
  "譽": "誉",
  "讓": "让",
  "負": "负",
  "責": "责",
  "買": "买",
  "這": "这",
  "進": "进",
  "過": "过",
  "選": "择",
  "還": "还",
  "釋": "释",
  "錯": "错",
  "門": "门",
  "開": "开",
  "關": "关",
  "際": "际",
  "難": "难",
  "順": "顺",
  "頭": "头",
  "願": "愿",
  "顧": "顾",
  "體": "体",
  "鬱": "郁",
  "麵": "面",
  "麼": "么"
};

function toSimplified(text: string): string {
  return [...text].map((ch) => TRAD_TO_SIMP[ch] ?? ch).join("");
}

function maybeSimplify(text: string, lang: string): string {
  if (lang === "zh-Hans") return toSimplified(text);
  return text;
}

function isPursuitIndirect(message: string): boolean {
  const lower = message.toLowerCase();
  const keywords = [
    "追求", "女生", "男生", "喜歡", "喜欢", "传话", "傳話",
    "中间人", "中間人", "第三者", "中介", "媒人",
    "girl", "boy", "guy", "crush", "dating", "love", "loving", "pursuing", "pursue",
    "communicate", "communication", "ghost", "intermediary", "middleman",
    "mutual friend", "third party", "text back",
  ];
  return keywords.some((k) => message.includes(k) || lower.includes(k));
}

function scenarioCopyEn(emotion: string, message: string): Record<string, string> {
  if (emotion === "social_conflict" && isPursuitIndirect(message)) {
    return {
      ack: "Feeling tired and shut out when she won't communicate directly is understandable.",
      not_control: "Whether she replies directly, how she distances herself, or uses others to pass messages.",
      in_control: "Whether you express yourself clearly once, with dignity, and how long you keep investing.",
      reframe: "You cannot command her response, but you can choose how you act without being dragged into endless guessing.",
      action: 'Say once, politely: "If you are open to it, I would like to talk directly." Then stop pushing.',
      question: "If direct contact never happens, what deadline would you give yourself?",
    };
  }
  if (emotion === "social_conflict" || emotion === "reputation") {
    return {
      ack: "Feeling hurt or stuck in a relationship is worth taking seriously.",
      not_control: "How others see you and how they choose to engage.",
      in_control: "Your tone, your boundaries, and whether you keep investing here.",
      reframe: "Reputation lives outside you; your character and actions live within.",
      action: "Today: say what you mean once, in a way you can stand behind.",
      question: "Apart from her reaction, who do you want to be in this?",
    };
  }
  return {
    ack: "I hear the frustration in what you shared.",
    not_control: "Others' choices, timing, and how they see you.",
    in_control: "Your goals, values, and the next small action you own today.",
    reframe: "Put energy into internal aims; let outcomes follow as they may.",
    action: "Do one small thing today that is fully within your control.",
    question: "What is one step you can actually move forward right now?",
  };
}

function scenarioCopy(emotion: string, message: string, lang: string): Record<string, string> {
  if (lang === "en") return scenarioCopyEn(emotion, message);
  if (emotion === "social_conflict" && isPursuitIndirect(message)) {
    return {
      ack: "一直要透過中間人傳話，感到鬱悶、像被擋在外面，這很自然。",
      not_control: "她是否願意直接和你說話、用什麼方式回應你",
      in_control: "你是否清楚、有分寸地表明意圖一次，以及如何解讀沉默、是否繼續投入",
      reframe: "你無法命令別人怎麼回應，但可以決定自己如何行動，而不被猜測拖垮。",
      action: "禮貌說一次：「若方便，我想直接和你聊幾句。」說完即可，不反覆追問。",
      question: "若始終沒有直接互動，你願意給自己一個等待的期限嗎？",
    };
  }
  if (emotion === "social_conflict" || emotion === "reputation") {
    return {
      ack: "在人際裡感到委屈或無奈，這種感受值得被正視。",
      not_control: "他人如何看待你、選擇怎麼與你相處",
      in_control: "你是否維持分寸與善意、是否繼續投入這段關係",
      reframe: "名聲與回應方式在外部；你的品格與行動在內部。",
      action: "今天只做一件小事：用你認可的語氣，把話說清楚一次。",
      question: "撇開對方的反應，你想成為什麼樣的自己？",
    };
  }
  if (emotion === "insult") {
    return {
      ack: "被冒犯時感到憤怒或難堪，都很正常。",
      not_control: "別人說了什麼、懷著什麼動機",
      in_control: "你如何判斷真假、是否回應、是否讓它佔據你一整天",
      reframe: "若話屬實，就改進；若不實，那是對方的誤解，不必用情緒買單。",
      action: "今天把注意力放回一件對你有價值的事上。",
      question: "若這句話一年後無人記得，你還想讓它困住你嗎？",
    };
  }
  if (emotion === "grief") {
    return {
      ack: "失去與哀傷需要時間，不必催促自己立刻好起來。",
      not_control: "已經發生的事、別人的離去或改變",
      in_control: "你如何紀念、如何照顧自己、如何一步步恢復日常",
      reframe: "悲痛不是敵人；理性要削減的是過分且不必要的部分。",
      action: "今天做一件小事：好好吃一餐、寫下一段你想記住的事。",
      question: "若對方仍在，你會希望被怎樣記得？",
    };
  }
  if (emotion === "anger") {
    return {
      ack: "怒火升起時，身體往往比頭腦更快。",
      not_control: "別人做了什麼、世事如何變化",
      in_control: "你如何詮釋、是否回擊、是否把今天交給憤怒",
      reframe: "生命太短，不值得把心力耗在可忽略的刺激上。",
      action: "先慢三次呼吸，再決定要不要回應。",
      question: "十年後回看，這件事還值得你今天如此激動嗎？",
    };
  }
  return {
    ack: "聽見你的無奈，這種感受很自然。",
    not_control: "他人的選擇、結果何時到來、別人怎麼看你",
    in_control: "你的目標、價值觀、今天具體的行動與態度",
    reframe: "把力氣用在內在目標上，外在結果順其自然。",
    action: "今天只做一件你能完全負責的小事。",
    question: "此刻，什麼是你真正能向前推進的一步？",
  };
}

export type ComposeOptions = {
  lang?: string;
  mode?: string;
  emotion?: string;
  weakContext?: boolean;
};

export function composeReply(
  userMessage: string,
  options: ComposeOptions = {},
): string {
  const lang = options.lang ?? "zh-Hant";
  const mode = options.mode ?? "feel";
  const emotion = options.emotion ?? "general";
  const weakContext = options.weakContext ?? false;

  if (lang === "en") {
    if (mode === "decide") {
      let body =
        "Let's sort the situation:\n\n" +
        "**In your control**: Your actions, attitude, and choices.\n" +
        "**Not in your control**: Others' reactions and final outcomes.\n\n" +
        "If you could only do one thing, which would you pick?";
      if (weakContext) {
        body += "\n\n(I couldn't find a strong passage — this is general Stoic framing.)";
      }
      return body;
    }
    const copy = scenarioCopy(emotion, userMessage, "en");
    let body =
      `Acknowledge: ${copy.ack}\n\n` +
      `Not in your control: ${copy.not_control}\n` +
      `In your control: ${copy.in_control}\n\n` +
      `Stoic reframe: ${copy.reframe}\n\n` +
      `One small step today: ${copy.action}\n\n` +
      `${copy.question}`;
    if (weakContext) {
      body += "\n\n(I couldn't find a strong passage — this is general Stoic framing.)";
    }
    return body;
  }

  if (mode === "decide") {
    let body =
      "先把處境整理如下：\n\n" +
      "可控：你的行動、態度與選擇。\n\n" +
      "不可控：他人的反應與最終結果。\n\n" +
      "若只能做一件事，你會選哪一個？";
    if (weakContext) {
      body += "\n\n（未找到強相關段落，以下為一般斯多葛框架。）";
    }
    return maybeSimplify(body, lang);
  }

  const copy = scenarioCopy(emotion, userMessage, "zh-Hant");
  let body =
    `承認情緒：${copy.ack}\n\n` +
    `不可控：${copy.not_control}\n` +
    `可控：${copy.in_control}\n\n` +
    `斯多葛重述：${copy.reframe}\n\n` +
    `今天可做的一件小事：${copy.action}\n\n` +
    `${copy.question}`;
  if (weakContext) {
    body += "\n\n（未找到強相關段落，以下為一般斯多葛框架。）";
  }
  return maybeSimplify(body, lang);
}
