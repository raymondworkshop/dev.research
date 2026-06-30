import { LANG_OPTIONS, type Lang } from '../lib/i18n'

interface Props {
  value: Lang
  onChange: (lang: Lang) => void
}

export function LangSelector({ value, onChange }: Props) {
  return (
    <div
      className="inline-flex rounded-full bg-stone-200/50 p-0.5 ring-1 ring-stone-200/80"
      role="radiogroup"
      aria-label="Reply language"
    >
      {LANG_OPTIONS.map((opt) => {
        const active = value === opt.value
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            title={opt.hint}
            onClick={() => onChange(opt.value)}
            className={[
              'rounded-full px-2.5 py-1 text-[11px] font-medium transition-all duration-200',
              active
                ? 'bg-white text-stone-800 shadow-sm ring-1 ring-stone-200/60'
                : 'text-stone-500 hover:text-stone-700',
            ].join(' ')}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
