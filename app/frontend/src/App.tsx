import { AskPage } from './pages/AskPage'
import { WikiIndex } from './pages/WikiIndex'
import { WikiPage } from './pages/WikiPage'
import { currentSlug, usePath } from './lib/path'

export default function App() {
  const path = usePath()
  const slug = currentSlug(path)

  if (!slug || slug === 'INDEX' || slug === 'index') return <WikiIndex />
  if (slug === 'ask') return <AskPage />
  return <WikiPage slug={slug} />
}
