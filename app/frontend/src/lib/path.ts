import { useEffect, useState } from 'react'

export function navigate(to: string) {
  const url = to.startsWith('/') ? to : `/${to}`
  if (url === window.location.pathname) return
  window.history.pushState({}, '', url)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

export function wikiHref(slug: string): string {
  if (!slug || slug === 'INDEX' || slug === 'index') return '/'
  return `/${slug}`
}

export function usePath(): string {
  const [path, setPath] = useState(() => window.location.pathname)
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  return path
}

export function currentSlug(path: string): string {
  return path.replace(/^\//, '').replace(/\/$/, '')
}
