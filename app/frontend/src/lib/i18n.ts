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
    tagline: '在可控處用力',
    subtitle: '用斯多葛哲思整理情緒',
    placeholder: '說說此刻的感受…',
    send: '送出',
    newChat: '新對話',
    disclaimer: '哲學反思輔助，非醫療服務',
    starters: [
      { label: '憤怒', text: '堵車時我很容易暴怒，事後又後悔。' },
      { label: '悲痛', text: '親人剛去世，悲痛停不下來。' },
      { label: '被冒犯', text: '同事在會議上當眾羞辱我。' },
      { label: '焦慮', text: '我很擔心別人的評價，做事總怕出錯。' },
    ],
  },
  'zh-Hans': {
    tagline: '在可控处用力',
    subtitle: '用斯多葛哲思整理情绪',
    placeholder: '说说此刻的感受…',
    send: '发送',
    newChat: '新对话',
    disclaimer: '哲学反思辅助，非医疗服务',
    starters: [
      { label: '愤怒', text: '堵车时我很容易暴怒，事后又后悔。' },
      { label: '悲痛', text: '亲人刚去世，悲痛停不下来。' },
      { label: '被冒犯', text: '同事在会议上当众羞辱我。' },
      { label: '焦虑', text: '我很担心别人的评价，做事总怕出错。' },
    ],
  },
  en: {
    tagline: 'Focus where you have agency',
    subtitle: 'Stoic reflection for everyday emotions',
    placeholder: 'What are you feeling right now?',
    send: 'Send',
    newChat: 'New chat',
    disclaimer: 'Philosophical reflection — not medical care',
    starters: [
      { label: 'Anger', text: 'I lose my temper in traffic and regret it afterward.' },
      { label: 'Grief', text: 'Someone close died and the grief won’t let up.' },
      { label: 'Insult', text: 'A colleague humiliated me in a meeting.' },
      { label: 'Anxiety', text: 'I worry constantly about what others think of me.' },
    ],
  },
}

export function uiLang(lang: Lang): UiKey {
  return lang
}

export function t(lang: Lang) {
  return UI[uiLang(lang)]
}
