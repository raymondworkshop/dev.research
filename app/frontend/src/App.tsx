import { useState } from 'react'
import { Chat } from './components/Chat'
import { ChatComposer } from './components/ChatComposer'
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

  const composer = (centerChips = false) => (
    <ChatComposer
      lang={lang}
      input={input}
      placeholder={ui.placeholder}
      sendLabel={ui.send}
      streaming={streaming}
      onInputChange={setInput}
      onSend={handleSend}
      onChipSelect={send}
      centerChips={centerChips}
    />
  )

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

      {empty ? (
        <main className="flex min-h-0 flex-1 flex-col items-center justify-center px-4 pb-8">
          <Hero lang={lang} />
          <div className="mt-10 w-full">{composer(true)}</div>
          <p className="mt-4 text-center text-[11px] leading-relaxed text-stone-400">
            {ui.disclaimer}
          </p>
        </main>
      ) : (
        <>
          <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <div className="flex min-h-0 flex-1 flex-col px-4 pt-2">
              <Chat messages={messages} streaming={streaming} lang={lang} />
            </div>
          </main>
          <footer className="sticky bottom-0 border-t border-stone-200/50 bg-[#f4f1ea]/90 px-4 pt-3 pb-4 backdrop-blur-md">
            {composer()}
            <p className="mt-2.5 text-center text-[11px] leading-relaxed text-stone-400">
              {ui.disclaimer}
            </p>
          </footer>
        </>
      )}
    </div>
  )
}
