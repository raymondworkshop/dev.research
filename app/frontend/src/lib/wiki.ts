export type WikiItem = { slug: string; summary: string }
export type WikiSection = { title: string; book?: string; items: WikiItem[] }

export function parseIndex(md: string): WikiSection[] {
  const sections: WikiSection[] = []
  let current: WikiSection | null = null
  for (const line of md.split('\n')) {
    const h2 = line.match(/^##\s+(.+)$/)
    if (h2) {
      const raw = h2[1].trim()
      const m = raw.match(/^(.+?)\s*\((.+)\)$/)
      current = {
        title: m ? m[1].trim() : raw,
        book: m ? m[2].replace(/\*/g, '').trim() : undefined,
        items: [],
      }
      sections.push(current)
      continue
    }
    const item = line.match(/^- \[\[([^\]]+)\]\](?:\s*-\s*(.*))?$/)
    if (item && current) {
      current.items.push({ slug: item[1].trim(), summary: (item[2] ?? '').trim() })
    }
  }
  return sections
}

export function pageTitle(slug: string, md: string): string {
  const h = md.match(/^#\s+(.+)$/m)
  if (h) return h[1].trim()
  return slug.replace(/-/g, ' ')
}

export function wikiToMarkdown(src: string): string {
  return src.replace(/\[\[([^\]]+)\]\]/g, (_, inner: string) => {
    const [slugPart, labelPart] = inner.split('|')
    const slug = slugPart.trim()
    const label = (labelPart ?? slug).trim()
    const href = !slug || slug === 'INDEX' || slug === 'index' ? '/' : `/${slug}`
    return `[${label}](${href})`
  })
}
