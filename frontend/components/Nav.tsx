'use client'

import Link from 'next/link'
import Image from 'next/image'
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
        <Link href="/" className="nav-brand" aria-label="Distressed Credit Signals">
          <Image
            className="nav-lockup nav-lockup-light"
            src="/brand/lockup.svg"
            width={300}
            height={32}
            alt=""
            aria-hidden="true"
            priority
            unoptimized
          />
          <Image
            className="nav-lockup nav-lockup-dark"
            src="/brand/lockup-dark.svg"
            width={300}
            height={32}
            alt=""
            aria-hidden="true"
            priority
            unoptimized
          />
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
