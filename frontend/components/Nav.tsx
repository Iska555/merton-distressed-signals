'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const LINKS = [
  { href: '/model', label: 'Model' },
  { href: '/mispricing', label: 'Mispricing' },
  { href: '/measurement', label: 'Measurement' },
  { href: '/evidence', label: 'Evidence' },
  { href: '/discrimination', label: 'Discrimination' },
  { href: '/case-studies', label: 'Cases' },
  { href: '/data', label: 'Data' },
]

export default function Nav() {
  const pathname = usePathname()
  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link href="/" className="nav-brand">
          Distressed Credit Signals
        </Link>
        <div className="nav-links">
          {LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              data-active={pathname === href || pathname.startsWith(href + '/')}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
