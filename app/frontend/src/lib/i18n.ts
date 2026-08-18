export type Lang = 'zh-Hant' | 'zh-Hans' | 'en'

export const LANG_OPTIONS: {
  value: Lang
  label: string
  hint: string
}[] = [
  { value: 'zh-Hant', label: '繁體', hint: 'Traditional Chinese' },
  { value: 'zh-Hans', label: '简体', hint: 'Simplified Chinese' },
  { value: 'en', label: 'English', hint: 'Replies in English' },
]

type UiKey = 'zh-Hant' | 'zh-Hans' | 'en'

const UI: Record<
  UiKey,
  {
    tagline: string
    subtitle: string
    placeholder: string
    send: string
    newChat: string
    disclaimer: string
    starters: { label: string; text: string }[]
  }
> = {
  'zh-Hant': {
    tagline: '對照 wiki 與筆記',
    subtitle: '回答會引用 wiki 頁與 notes/（raw）',
    placeholder: '問一個主題，核對原文…',
    send: '送出',
    newChat: '新對話',
    disclaimer: '以你的 wiki 與 notes/ 為準，不是通用建議',
    starters: [
      { label: '學習型對話', text: '什麼是 learning conversation？該怎麼開始一場困難對話？' },
      { label: '存錢', text: '筆記裡怎麼說儲蓄率與自我？' },
      { label: '傾聽', text: 'Charm 裡傾聽要做哪些動作？' },
      { label: '身份', text: '困難對話裡 identity conversation 是什麼？' },
    ],
  },
  'zh-Hans': {
    tagline: '对照 wiki 与笔记',
    subtitle: '回答会引用 wiki 页与 notes/（raw）',
    placeholder: '问一个主题，核对原文…',
    send: '发送',
    newChat: '新对话',
    disclaimer: '以你的 wiki 与 notes/ 为准，不是通用建议',
    starters: [
      { label: '学习型对话', text: '什么是 learning conversation？该怎么开始一场困难对话？' },
      { label: '存钱', text: '笔记里怎么说储蓄率与自我？' },
      { label: '倾听', text: 'Charm 里倾听要做哪些动作？' },
      { label: '身份', text: '困难对话里 identity conversation 是什么？' },
    ],
  },
  en: {
    tagline: 'Check the wiki against notes',
    subtitle: 'Replies cite wiki pages and notes/ (raw)',
    placeholder: 'Ask a theme, then check the source…',
    send: 'Send',
    newChat: 'New chat',
    disclaimer: 'Grounded in your wiki and notes/ — not generic advice',
    starters: [
      { label: 'Learning talk', text: 'What is a learning conversation and how do I start a difficult one?' },
      { label: 'Saving', text: 'What do the notes say about savings rate and ego?' },
      { label: 'Listening', text: 'What does Charm say you should do when listening?' },
      { label: 'Identity', text: 'What is the identity conversation in Difficult Conversations?' },
    ],
  },
}

export function uiLang(lang: Lang): UiKey {
  return lang
}

export function t(lang: Lang) {
  return UI[uiLang(lang)]
}
