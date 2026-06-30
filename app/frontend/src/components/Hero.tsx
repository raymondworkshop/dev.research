import type { Lang } from '../lib/i18n'
import { t } from '../lib/i18n'

interface Props {
  lang: Lang
}

export function Hero({ lang }: Props) {
  const { tagline, subtitle } = t(lang)

  return (
    <div className="flex flex-col items-center px-6 text-center">
      <p
        className="select-none text-[3.25rem] font-extralight leading-none text-stone-300"
        aria-hidden
      >
        穩
      </p>
      <p className="mt-8 text-[15px] font-medium tracking-[0.12em] text-stone-700">{tagline}</p>
      <p className="mt-2.5 max-w-[16rem] text-[13px] leading-relaxed text-stone-400">
        {subtitle}
      </p>
    </div>
  )
}
