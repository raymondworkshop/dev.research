import { useState } from 'react'
import { Chat } from '../components/Chat'
import { ChatComposer } from '../components/ChatComposer'
import { SiteHeader } from '../components/SiteHeader'
import { useChatStream } from '../hooks/useChatStream'
import type { Lang } from '../lib/i18n'
import { t } from '../lib/i18n'
import { LangSelector } from '../components/LangSelector'

export function AskPage() {
  const [lang, setLang] = useState<Lang>('zh-Hant')
  const [input, setInput] = useState('')
  const { messages, streaming, send, reset } = useChatStream(lang)
  const ui = t(lang)
  const empty = messages.length === 0

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    send(text)
  }

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
    <div className="relative min-h-screen">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[#f4f1ea]" />
      <SiteHeader active="ask" />
      <div className="mx-auto flex min-h-[calc(100vh-3.25rem)] max-w-lg flex-col">
      <div className="flex items-center justify-end gap-2 px-4 pt-3">
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

      {empty ? (
        <main className="flex min-h-0 flex-1 flex-col items-center justify-center px-4 pb-8">
          <p className="text-[15px] font-medium tracking-wide text-stone-700">{ui.tagline}</p>
          <p className="mt-2 max-w-[18rem] text-center text-[13px] leading-relaxed text-stone-400">
            {ui.subtitle}
          </p>
          <div className="mt-10 w-full">{composer(true)}</div>
          <p className="mt-4 text-center text-[11px] leading-relaxed text-stone-400">{ui.disclaimer}</p>
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
            <p className="mt-2.5 text-center text-[11px] leading-relaxed text-stone-400">{ui.disclaimer}</p>
          </footer>
        </>
      )}
      </div>
    </div>
  )
}
