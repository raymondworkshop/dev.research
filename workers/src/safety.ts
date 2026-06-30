export const CRISIS_KEYWORDS = [
  "自杀", "自殺", "想死", "不想活", "了结", "了結", "结束生命", "結束生命",
  "suicide", "kill myself", "end my life", "self-harm", "self harm",
  "hurt myself", "want to die",
];

const HOTLINES: Record<string, string[]> = {
  "zh-Hant": [
    "台灣 1925 安心專線",
    "生命線 1995",
    "張老師 1980",
  ],
  "zh-Hans": [
    "北京心理危机研究与干预中心 010-82951332",
    "全国心理援助热线 12356",
  ],
  en: [
    "988 Suicide & Crisis Lifeline (US)",
    "Samaritans 116 123 (UK)",
  ],
};

export function checkCrisis(message: string): boolean {
  const lower = message.toLowerCase();
  return CRISIS_KEYWORDS.some((kw) => message.includes(kw) || lower.includes(kw));
}

export function crisisResponse(lang: string = "zh-Hant"): string {
  const lines = HOTLINES[lang] ?? HOTLINES["zh-Hant"];
  const header: Record<string, string> = {
    "zh-Hant": "若你正在經歷嚴重痛苦，請聯繫專業協助：",
    "zh-Hans": "若你正在经历严重痛苦，请联系专业协助：",
    en: "If you are in crisis, please contact professional support:",
  };
  const footer: Record<string, string> = {
    "zh-Hant": "本工具無法提供危機支援。",
    "zh-Hans": "本工具无法提供危机支援。",
    en: "This tool cannot provide crisis support.",
  };
  const h = header[lang] ?? header["zh-Hant"];
  const body = lines.map((line) => `· ${line}`).join("\n");
  const f = footer[lang] ?? "";
  return `${h}\n${body}\n\n${f}`;
}
