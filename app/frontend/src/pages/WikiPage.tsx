import { wikiPages } from 'virtual:wiki'
import { SiteHeader } from '../components/SiteHeader'
import { renderWikiMarkdown } from '../lib/markdown'
import { navigate } from '../lib/path'

export function WikiPage({ slug }: { slug: string }) {
  const md = wikiPages[slug]
  if (!md) {
    return (
      <div className="mx-auto min-h-screen max-w-[40rem] px-[clamp(1rem,4vw,2rem)] pt-[clamp(1.25rem,5vw,3.25rem)] pb-16">
        <SiteHeader active="page" />
        <main className="pt-[clamp(1.8rem,4vw,2.6rem)]">
          <p className="text-[#8a8f96]">No page named {slug}.</p>
        </main>
      </div>
    )
  }

  const html = renderWikiMarkdown(md)

  return (
    <div className="mx-auto min-h-screen max-w-[40rem] px-[clamp(1rem,4vw,2rem)] pt-[clamp(1.25rem,5vw,3.25rem)] pb-16">
      <SiteHeader active="page" />
      <main className="pt-[clamp(1.8rem,4vw,2.6rem)]">
        <nav className="reading-nav" aria-label="Section">
          <a
            href="/"
            onClick={(e) => {
              e.preventDefault()
              navigate('/')
            }}
          >
            ← Index
          </a>
        </nav>
        <h1 className="mb-6 text-[clamp(1.35rem,3vw,1.65rem)] font-semibold tracking-tight text-[#1a1d21]">
          {slug}
        </h1>
        <article
          className="wiki-prose"
          dangerouslySetInnerHTML={{ __html: html }}
          onClick={(e) => {
            const a = (e.target as HTMLElement).closest('a')
            if (!a) return
            const href = a.getAttribute('href')
            if (!href?.startsWith('/')) return
            e.preventDefault()
            navigate(href)
          }}
        />
      </main>
    </div>
  )
}
