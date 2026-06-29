import { useState } from 'react'
import type { ChatMessage, Citation } from '../hooks/useChatStream'

interface Props {
  messages: ChatMessage[]
  streaming: boolean
}

function Citations({ items }: { items: Citation[] }) {
  const [open, setOpen] = useState(false)
  if (!items.length) return null

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-[11px] text-stone-400 hover:text-stone-600"
      >
        {open ? '收起引用' : `引用 · ${items.length}`}
      </button>
      {open && (
        <ul className="mt-1 space-y-0.5 pl-0 list-none">
          {items.map((c) => (
            <li key={c.id} className="text-[11px] text-stone-500">
              {c.title}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function Chat({ messages, streaming }: Props) {
  return (
    <div className="flex flex-1 flex-col gap-5 overflow-y-auto">
      {messages.length === 0 && (
        <p className="text-center text-sm text-stone-400 pt-8">
          在可控处用力
        </p>
      )}
      {messages.map((msg, i) => (
        <div
          key={i}
          className={
            msg.role === 'user'
              ? 'ml-8 text-right'
              : msg.crisis
                ? 'rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-900'
                : ''
          }
        >
          {msg.role === 'user' ? (
            <span className="inline-block rounded-2xl bg-stone-800 px-3 py-2 text-sm text-white text-left">
              {msg.content}
            </span>
          ) : (
            <div className="text-sm leading-relaxed text-stone-800 whitespace-pre-wrap">
              {msg.content ||
                (msg.status && i === messages.length - 1 ? (
                  <span className="text-stone-400">{msg.status}</span>
                ) : streaming && i === messages.length - 1 ? (
                  '…'
                ) : (
                  ''
                ))}
              {msg.citations && msg.citations.length > 0 && (
                <Citations items={msg.citations} />
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
