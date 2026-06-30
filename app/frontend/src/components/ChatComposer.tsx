import { EmotionChips } from './EmotionChips'
import type { Lang } from '../lib/i18n'

interface Props {
  lang: Lang
  input: string
  placeholder: string
  sendLabel: string
  streaming: boolean
  onInputChange: (value: string) => void
  onSend: () => void
  onChipSelect: (text: string) => void
  centerChips?: boolean
}

export function ChatComposer({
  lang,
  input,
  placeholder,
  sendLabel,
  streaming,
  onInputChange,
  onSend,
  onChipSelect,
  centerChips,
}: Props) {
  return (
    <>
      <EmotionChips lang={lang} onSelect={onChipSelect} disabled={streaming} centered={centerChips} />
      <div className="mt-2.5 flex items-end gap-2 rounded-2xl bg-white/80 p-1.5 shadow-sm ring-1 ring-stone-200/60">
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              onSend()
            }
          }}
          rows={1}
          placeholder={placeholder}
          disabled={streaming}
          className="max-h-32 flex-1 resize-none rounded-xl border-0 bg-transparent px-3 py-2.5 text-sm text-stone-800 outline-none placeholder:text-stone-400"
        />
        <button
          type="button"
          onClick={onSend}
          disabled={streaming || !input.trim()}
          aria-label={sendLabel}
          className="mb-0.5 flex h-10 min-w-10 items-center justify-center rounded-xl bg-stone-800 px-3 text-sm font-medium text-white shadow-sm transition hover:bg-stone-700 disabled:opacity-35"
        >
          ↑
        </button>
      </div>
    </>
  )
}
