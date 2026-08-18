import { marked } from 'marked'
import { wikiToMarkdown } from './wiki'

marked.setOptions({ gfm: true, breaks: false })

export function renderWikiMarkdown(src: string): string {
  const html = marked.parse(wikiToMarkdown(src), { async: false }) as string
  return html
    .replace(/<a href="(\/[^"]*)"/g, '<a data-wiki="1" href="$1"')
    .replace(/<a href="(https?:[^"]*)"/g, '<a target="_blank" rel="noreferrer" href="$1"')
}
