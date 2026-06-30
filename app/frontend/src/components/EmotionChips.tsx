import type { Lang } from '../lib/i18n'
import { t } from '../lib/i18n'

interface Props {
  lang: Lang
  onSelect: (text: string) => void
  disabled?: boolean
}

export function EmotionChips({ lang, onSelect, disabled }: Props) {
  const { starters } = t(lang)

  return (
    <div className="flex flex-wrap justify-center gap-x-5 gap-y-2">
      {starters.map((s) => (
        <button
          key={s.label}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(s.text)}
          className="rounded-full px-3.5 py-1.5 text-[13px] text-stone-500 transition hover:text-stone-800 disabled:opacity-40"
        >
          {s.label}
        </button>
      ))}
    </div>
  )
}
