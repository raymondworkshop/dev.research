import { useState } from 'react'
import { Chat } from './components/Chat'
import { EmotionChips } from './components/EmotionChips'
import { useChatStream } from './hooks/useChatStream'

type Lang = 'auto' | 'zh-Hant' | 'zh-Hans' | 'en'

const LANG_LABEL: Record<Lang, string> = {
  auto: '自动',
  'zh-Hant': '繁',
  'zh-Hans': '简',
  en: 'EN',
}

export default function App() {
  const [lang, setLang] = useState<Lang>('auto')
  const [input, setInput] = useState('')
  const { messages, streaming, send, reset } = useChatStream(lang)

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    send(text)
  }

  const empty = messages.length === 0

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col">
      <header className="flex items-center justify-between px-4 py-3">
        <h1 className="text-base font-medium text-stone-800">穩心</h1>
        <div className="flex items-center gap-3 text-xs text-stone-500">
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value as Lang)}
            className="bg-transparent outline-none cursor-pointer"
          >
            {(Object.keys(LANG_LABEL) as Lang[]).map((l) => (
              <option key={l} value={l}>
                {LANG_LABEL[l]}
              </option>
            ))}
          </select>
          {!empty && (
            <button
              type="button"
              onClick={reset}
              disabled={streaming}
              className="hover:text-stone-800 disabled:opacity-40"
            >
              新对话
            </button>
          )}
        </div>
      </header>

      <main className="flex flex-1 flex-col gap-4 overflow-hidden px-4 pb-2">
        {empty && <EmotionChips onSelect={send} disabled={streaming} />}
        <Chat messages={messages} streaming={streaming} />
      </main>

      <footer className="sticky bottom-0 border-t border-stone-200/60 bg-[#f8f6f2] px-4 pt-3 pb-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            rows={1}
            placeholder="说说此刻的感受…"
            disabled={streaming}
            className="flex-1 resize-none rounded-lg border-0 bg-white px-3 py-2.5 text-sm shadow-sm outline-none ring-1 ring-stone-200 focus:ring-stone-400"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={streaming || !input.trim()}
            className="rounded-lg bg-stone-800 px-3 py-2.5 text-sm text-white disabled:opacity-40"
          >
            →
          </button>
        </div>
        <p className="mt-2 text-center text-[11px] text-stone-400">
          哲学反思辅助，非医疗服务 · 本地处理
        </p>
      </footer>
    </div>
  )
}
