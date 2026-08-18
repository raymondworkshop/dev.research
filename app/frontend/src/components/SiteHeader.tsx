import type { ReactNode } from 'react'
import { navigate } from '../lib/path'

export function SiteHeader({ active }: { active: 'index' | 'ask' | 'page' }) {
  return (
    <header className="sticky top-0 z-10 border-b border-stone-200/50 bg-[#f4f1ea]/90 px-4 py-3 backdrop-blur-md">
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault()
            navigate('/')
          }}
          className="text-base font-semibold tracking-tight text-stone-800"
        >
          Wiki Research
        </a>
        <nav className="flex items-center gap-1 text-[13px]">
          <NavLink href="/" current={active === 'index' || active === 'page'}>
            Index
          </NavLink>
          <NavLink href="/ask" current={active === 'ask'}>
            Ask
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

function NavLink({
  href,
  current,
  children,
}: {
  href: string
  current: boolean
  children: ReactNode
}) {
  return (
    <a
      href={href}
      onClick={(e) => {
        e.preventDefault()
        navigate(href)
      }}
      className={
        current
          ? 'rounded-full bg-white/80 px-3 py-1 font-medium text-stone-800 shadow-sm ring-1 ring-stone-200/70'
          : 'rounded-full px-3 py-1 text-stone-500 hover:text-stone-800'
      }
    >
      {children}
    </a>
  )
}
