import { navigate } from '../lib/path'

export function SiteHeader({ active }: { active: 'index' | 'ask' | 'page' }) {
  const link = active === 'ask' ? { href: '/', label: 'Index' } : { href: '/ask', label: 'Ask' }

  return (
    <header>
      <nav className="flex items-baseline justify-between gap-6" aria-label="Primary">
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault()
            navigate('/')
          }}
          className="text-base font-medium tracking-tight text-[#1a1d21] no-underline hover:text-[#174033]"
        >
          Notes
        </a>
        <a
          href={link.href}
          onClick={(e) => {
            e.preventDefault()
            navigate(link.href)
          }}
          className="text-[0.88rem] text-[#8a8f96] no-underline hover:text-[#174033]"
        >
          {link.label}
        </a>
      </nav>
    </header>
  )
}
