export const EMOTION_KEYWORDS: Record<string, string[]> = {
  anger: [
    "anger", "angry", "rage", "furious", "憤怒", "暴怒", "生气", "氣", "恼火",
  ],
  grief: [
    "grief", "grieve", "loss", "mourning", "悲痛", "悲伤", "悲傷", "去世", "失去",
  ],
  insult: [
    "insult", "offend", "humiliat", "羞辱", "侮辱", "冒犯", "被骂", "被罵",
  ],
  reputation: [
    "reputation", "opinion", "judgment", "judgement", "名声", "名聲", "评价", "評價",
  ],
  control: [
    "control", "controllable", "dichotomy", "可控", "控制", "二分", "无奈", "無奈", "郁闷", "鬱悶",
  ],
  social_conflict: [
    "conflict", "relationship", "social", "人际", "人際", "交往", "冲突", "衝突",
    "追求", "女生", "传话", "傳話", "中间人", "中間人",
    "girl", "boy", "guy", "crush", "dating", "love", "loving", "pursuing", "pursue",
    "communicate", "communication", "text back", "reply", "ghost", "ghosting",
    "intermediary", "middleman", "mutual friend", "third party",
    "tired", "exhausted", "drained",
  ],
  present_moment: [
    "present", "now", "moment", "当下", "當下", "活在", "现在", "現在",
  ],
  negative_visualization: [
    "negative visualization", "premeditatio", "消極想像", "消极想象", "预想", "預想",
  ],
};

const PRIORITY = [
  "social_conflict",
  "insult",
  "grief",
  "anger",
  "reputation",
  "control",
  "present_moment",
  "negative_visualization",
] as const;

const DECIDE_SIGNALS = [
  "should i", "what do i do", "怎么办", "怎麼辦", "该不该", "該不該", "decide", "选择", "選擇",
];

export function routeMessage(message: string): [string, string] {
  const lower = message.toLowerCase();
  const mode = DECIDE_SIGNALS.some((s) => lower.includes(s) || message.includes(s))
    ? "decide"
    : "feel";

  for (const emotion of PRIORITY) {
    const keywords = EMOTION_KEYWORDS[emotion] ?? [];
    for (const kw of keywords) {
      if (lower.includes(kw.toLowerCase()) || message.includes(kw)) {
        return [emotion, mode];
      }
    }
  }
  return ["general", mode];
}
