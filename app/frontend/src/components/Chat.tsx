import { useEffect, useRef, useState } from 'react'
import type { ChatMessage, Citation } from '../hooks/useChatStream'
import type { Lang } from '../lib/i18n'
import { StructuredReply } from './StructuredReply'

interface Props {
  messages: ChatMessage[]
  streaming: boolean
  lang: Lang
}

function Citations({ items, lang }: { items: Citation[]; lang: Lang }) {
  const [open, setOpen] = useState(false)
  const label = lang === 'en' ? 'Sources' : '引用'
  const toggle = lang === 'en' ? (open ? 'Hide' : 'Show') : open ? '收起' : '展開'

  if (!items.length) return null

  return (
    <div className="mt-3 border-t border-stone-200/60 pt-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-[11px] font-medium text-sage-700 hover:text-sage-900"
      >
        <span className="inline-block h-1 w-1 rounded-full bg-sage-500" />
        {label} · {items.length}
        <span className="text-stone-400">({toggle})</span>
      </button>
      {open && (
        <ul className="mt-2 space-y-1 pl-0 list-none">
          {items.map((c) => (
            <li
              key={c.id}
              className="rounded-md bg-stone-50/80 px-2 py-1 text-[11px] leading-snug text-stone-600"
            >
              {c.title}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function Chat({ messages, streaming, lang }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, streaming])

  if (messages.length === 0) return null

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto pb-4 scroll-smooth">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={
            msg.role === 'user'
              ? 'flex justify-end pl-10'
              : msg.crisis
                ? 'rounded-xl border border-red-200/80 bg-red-50/90 px-4 py-3 text-red-900 shadow-sm'
                : 'flex justify-start pr-6'
          }
        >
          {msg.role === 'user' ? (
            <span className="inline-block max-w-[92%] rounded-2xl rounded-br-md bg-stone-800 px-4 py-2.5 text-sm leading-relaxed text-white shadow-md">
              {msg.content}
            </span>
          ) : (
            <div className="max-w-full rounded-2xl rounded-bl-md border border-stone-200/50 bg-white/80 px-4 py-3 text-sm text-stone-800 shadow-sm backdrop-blur-sm">
              {msg.content ? (
                <StructuredReply
                  content={msg.content}
                  lang={lang}
                  streaming={streaming && i === messages.length - 1}
                />
              ) : msg.status && i === messages.length - 1 ? (
                <span className="inline-flex items-center gap-2 text-stone-400">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-sage-400" />
                  {msg.status}
                </span>
              ) : streaming && i === messages.length - 1 ? (
                <span className="text-stone-400">…</span>
              ) : null}
              {msg.citations && msg.citations.length > 0 && (
                <Citations items={msg.citations} lang={lang} />
              )}
            </div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
