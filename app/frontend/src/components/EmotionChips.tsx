import type { Lang } from '../lib/i18n'
import { t } from '../lib/i18n'

interface Props {
  lang: Lang
  onSelect: (text: string) => void
  disabled?: boolean
  centered?: boolean
}

export function EmotionChips({ lang, onSelect, disabled, centered }: Props) {
  const { starters } = t(lang)

  return (
    <div className={`mb-1 flex flex-wrap gap-2 ${centered ? 'justify-center' : ''}`}>
      {starters.map((s) => (
        <button
          key={s.label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(s.text)}
          className="rounded-full bg-white/70 px-3 py-1 text-[12px] text-stone-600 ring-1 ring-stone-200/70 transition hover:bg-white hover:text-stone-800 disabled:opacity-40"
        >
          {s.label}
        </button>
      ))}
    </div>
  )
}
