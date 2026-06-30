import { useState } from 'react'
import { Chat } from './components/Chat'
import { EmotionChips } from './components/EmotionChips'
import { Hero } from './components/Hero'
import { LangSelector } from './components/LangSelector'
import { useChatStream } from './hooks/useChatStream'
import type { Lang } from './lib/i18n'
import { t } from './lib/i18n'

export default function App() {
  const [lang, setLang] = useState<Lang>('zh-Hant')
  const [input, setInput] = useState('')
  const { messages, streaming, send, reset } = useChatStream(lang)
  const ui = t(lang)

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    send(text)
  }

  const empty = messages.length === 0

  return (
    <div className="relative mx-auto flex min-h-screen max-w-lg flex-col">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[#f4f1ea]" />
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_rgba(120,140,110,0.12)_0%,_transparent_55%)]" />

      <header className="sticky top-0 z-10 border-b border-stone-200/50 bg-[#f4f1ea]/85 px-4 py-3 backdrop-blur-md">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-base font-semibold tracking-tight text-stone-800">
              穩心
              <span className="ml-1.5 text-xs font-normal text-stone-400">Steady Mind</span>
            </h1>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <LangSelector value={lang} onChange={setLang} />
            {!empty && (
              <button
                type="button"
                onClick={reset}
                disabled={streaming}
                className="rounded-full px-2 py-1 text-[11px] font-medium text-stone-500 transition hover:bg-white/60 hover:text-stone-800 disabled:opacity-40"
              >
                {ui.newChat}
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {empty ? (
          <>
            <Hero lang={lang} />
            <div className="shrink-0 px-4 pb-6">
              <EmotionChips lang={lang} onSelect={send} disabled={streaming} />
            </div>
          </>
        ) : (
          <div className="flex min-h-0 flex-1 flex-col px-4 pt-2">
            <Chat messages={messages} streaming={streaming} lang={lang} />
          </div>
        )}
      </main>

      <footer className="sticky bottom-0 border-t border-stone-200/50 bg-[#f4f1ea]/90 px-4 pt-3 pb-4 backdrop-blur-md">
        <div className="flex items-end gap-2 rounded-2xl bg-white/80 p-1.5 shadow-sm ring-1 ring-stone-200/60">
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
            placeholder={ui.placeholder}
            disabled={streaming}
            className="max-h-32 flex-1 resize-none rounded-xl border-0 bg-transparent px-3 py-2.5 text-sm text-stone-800 outline-none placeholder:text-stone-400"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={streaming || !input.trim()}
            aria-label={ui.send}
            className="mb-0.5 flex h-10 min-w-10 items-center justify-center rounded-xl bg-stone-800 px-3 text-sm font-medium text-white shadow-sm transition hover:bg-stone-700 disabled:opacity-35"
          >
            ↑
          </button>
        </div>
        <p className="mt-2.5 text-center text-[11px] leading-relaxed text-stone-400">
          {ui.disclaimer}
        </p>
      </footer>
    </div>
  )
}
