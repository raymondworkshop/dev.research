import { wikiPages } from 'virtual:wiki'
import { SiteHeader } from '../components/SiteHeader'
import { navigate, wikiHref } from '../lib/path'
import { parseIndex } from '../lib/wiki'

export function WikiIndex() {
  const sections = parseIndex(wikiPages.INDEX ?? '')

  return (
    <div className="relative min-h-screen">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[#f4f1ea]" />
      <SiteHeader active="index" />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <p className="text-[13px] tracking-[0.14em] text-stone-400 uppercase">Personal KB</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-800">Wiki Index</h1>
        <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-stone-500">
          Themes compiled from notes. Ask cites these pages and the raw notes behind them.
        </p>
        <div className="mt-10 space-y-10">
          {sections.map((section) => (
            <section key={section.title}>
              <h2 className="text-lg font-semibold text-stone-800">
                {section.title}
                {section.book ? (
                  <span className="ml-2 text-sm font-normal text-stone-400">{section.book}</span>
                ) : null}
              </h2>
              <ul className="mt-3 divide-y divide-stone-200/70">
                {section.items.map((item) => (
                  <li key={item.slug}>
                    <a
                      href={wikiHref(item.slug)}
                      onClick={(e) => {
                        e.preventDefault()
                        navigate(wikiHref(item.slug))
                      }}
                      className="flex flex-col gap-0.5 py-2.5 hover:bg-white/50 sm:flex-row sm:items-baseline sm:gap-3"
                    >
                      <span className="shrink-0 font-medium text-sage-700">{item.slug}</span>
                      {item.summary ? (
                        <span className="text-[14px] leading-relaxed text-stone-600">{item.summary}</span>
                      ) : null}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </main>
    </div>
  )
}
