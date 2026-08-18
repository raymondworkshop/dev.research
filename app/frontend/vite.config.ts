import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const here = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(here, '../..')
const WIKI_DIR = path.join(ROOT, 'wiki')
const NOTES_DIR = path.join(ROOT, 'notes')

type CorpusChunk = {
  id: string
  title: string
  source: 'wiki' | 'notes'
  slug?: string
  text: string
}

function loadWiki(): Record<string, string> {
  const out: Record<string, string> = {}
  if (!fs.existsSync(WIKI_DIR)) return out
  for (const f of fs.readdirSync(WIKI_DIR)) {
    if (!f.endsWith('.md')) continue
    const slug = f.replace(/\.md$/, '')
    out[slug] = fs.readFileSync(path.join(WIKI_DIR, f), 'utf8')
  }
  return out
}

function chunkText(text: string, size = 900): string[] {
  const paras = text.split(/\n{2,}/)
  const chunks: string[] = []
  let buf = ''
  for (const p of paras) {
    const piece = p.trim()
    if (!piece) continue
    if (buf.length + piece.length + 2 > size && buf) {
      chunks.push(buf)
      buf = piece
    } else {
      buf = buf ? `${buf}\n\n${piece}` : piece
    }
  }
  if (buf) chunks.push(buf)
  return chunks.length ? chunks : [text.slice(0, size)]
}

function buildCorpus(): CorpusChunk[] {
  const chunks: CorpusChunk[] = []
  const wiki = loadWiki()
  for (const [slug, text] of Object.entries(wiki)) {
    if (slug === 'INDEX') continue
    chunkText(text).forEach((part, i) => {
      chunks.push({
        id: `wiki:${slug}:${i}`,
        title: slug,
        source: 'wiki',
        slug,
        text: part,
      })
    })
  }
  if (fs.existsSync(NOTES_DIR)) {
    for (const f of fs.readdirSync(NOTES_DIR)) {
      if (!f.endsWith('.md')) continue
      const text = fs.readFileSync(path.join(NOTES_DIR, f), 'utf8')
      const title = f.replace(/\.md$/, '')
      chunkText(text, 800).forEach((part, i) => {
        chunks.push({
          id: `notes:${title}:${i}`,
          title: `notes/${f}`,
          source: 'notes',
          text: part,
        })
      })
    }
  }
  return chunks
}

function wikiBundle(): Plugin {
  const virtualId = 'virtual:wiki'
  const resolvedId = '\0' + virtualId

  return {
    name: 'wiki-bundle',
    resolveId(id) {
      if (id === virtualId) return resolvedId
    },
    load(id) {
      if (id === resolvedId) {
        return `export const wikiPages = ${JSON.stringify(loadWiki())}`
      }
    },
    configureServer(server) {
      server.watcher.add(WIKI_DIR)
      server.watcher.add(NOTES_DIR)
      const reload = (file: string) => {
        if (!file.startsWith(WIKI_DIR) && !file.startsWith(NOTES_DIR)) return
        const mod = server.moduleGraph.getModuleById(resolvedId)
        if (mod) server.moduleGraph.invalidateModule(mod)
        server.ws.send({ type: 'full-reload' })
      }
      server.watcher.on('change', reload)
      server.watcher.on('add', reload)
    },
    generateBundle() {
      this.emitFile({
        type: 'asset',
        fileName: 'corpus.json',
        source: JSON.stringify(buildCorpus()),
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), wikiBundle()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
    },
  },
})
