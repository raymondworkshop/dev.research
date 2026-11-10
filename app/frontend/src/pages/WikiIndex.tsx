import { wikiPages } from 'virtual:wiki'
import { SiteHeader } from '../components/SiteHeader'
import { navigate, wikiHref } from '../lib/path'
import { parseIndex } from '../lib/wiki'

export function WikiIndex() {
  const sections = parseIndex(wikiPages.INDEX ?? '')

  return (
    <div className="mx-auto min-h-screen max-w-[40rem] px-[clamp(1rem,4vw,2rem)] pt-[clamp(1.25rem,5vw,3.25rem)] pb-16">
      <SiteHeader active="index" />
      <main className="pt-[clamp(1.8rem,4vw,2.6rem)]">
        <h1 className="mb-3 text-[clamp(1.45rem,3.4vw,1.7rem)] font-semibold tracking-tight text-[#1a1d21]">
          Wiki Index
        </h1>
        {sections.map((section) => (
          <section key={section.title}>
            <h2 className="mt-8 mb-3 text-[clamp(1.2rem,2.5vw,1.35rem)] font-semibold tracking-tight text-[#1a1d21]">
              {section.title}
              {section.book ? (
                <>
                  {' '}
                  (<em>{section.book}</em>)
                </>
              ) : null}
            </h2>
            <ul className="mb-5 list-disc pl-[1.35rem] marker:text-[#8a8f96]">
              {section.items.map((item) => (
                <li key={item.slug} className="mb-[0.35rem]">
                  <a
                    href={wikiHref(item.slug)}
                    onClick={(e) => {
                      e.preventDefault()
                      navigate(wikiHref(item.slug))
                    }}
                    className="wikilink"
                  >
                    {item.slug}
                  </a>
                  {item.summary ? <span> - {item.summary}</span> : null}
                </li>
              ))}
            </ul>
          </section>
        ))}
      </main>
    </div>
  )
}
