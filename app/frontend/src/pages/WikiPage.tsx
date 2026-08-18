import { wikiPages } from 'virtual:wiki'
import { SiteHeader } from '../components/SiteHeader'
import { renderWikiMarkdown } from '../lib/markdown'
import { navigate } from '../lib/path'

export function WikiPage({ slug }: { slug: string }) {
  const md = wikiPages[slug]
  if (!md) {
    return (
      <div className="relative min-h-screen">
        <div className="pointer-events-none fixed inset-0 -z-10 bg-[#f4f1ea]" />
        <SiteHeader active="page" />
        <main className="mx-auto max-w-3xl px-4 py-16">
          <p className="text-stone-500">No page named {slug}.</p>
          <a
            href="/"
            className="mt-4 inline-block text-sage-700 hover:underline"
            onClick={(e) => {
              e.preventDefault()
              navigate('/')
            }}
          >
            Back to index
          </a>
        </main>
      </div>
    )
  }

  const html = renderWikiMarkdown(md)

  return (
    <div className="relative min-h-screen">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[#f4f1ea]" />
      <SiteHeader active="page" />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <a
          href="/"
          className="text-[13px] text-stone-400 hover:text-stone-700"
          onClick={(e) => {
            e.preventDefault()
            navigate('/')
          }}
        >
          ← Index
        </a>
        <article
          className="wiki-prose mt-4"
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
        <p className="mt-12 text-[12px] text-stone-400">
          <a
            href="/ask"
            className="hover:text-stone-600"
            onClick={(e) => {
              e.preventDefault()
              navigate('/ask')
            }}
          >
            Ask
          </a>{' '}
          to check this against notes/
        </p>
      </main>
    </div>
  )
}
