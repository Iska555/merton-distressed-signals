import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Link from 'next/link'
import MobileNav from '@/components/MobileNav'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Merton Credit Scanner',
  description: 'Real-time credit arbitrage signals using structural models',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" style={{ backgroundColor: 'black' }}>
      <head>
        {/* Set default zoom to 85% on mobile */}
        <meta 
          name="viewport" 
          content="width=device-width, initial-scale=0.85, maximum-scale=2.0, user-scalable=yes" 
        />
      </head>
      {/* Inline styles completely override globals.css to kill the gray gradient */}
      <body 
        className={`${inter.className} text-white min-h-screen`}
        style={{ backgroundColor: 'black', backgroundImage: 'none' }}
      >
        {/* Header */}
        <header className="border-b border-zinc-900 backdrop-blur-sm bg-black/50 sticky top-0 z-50">
          <div className="container mx-auto px-6 py-4">
            <nav className="flex items-center justify-between">
              {/* Logo */}
              <Link href="/">
                <div className="flex items-center gap-3 cursor-pointer group">
                  <div className="w-8 h-8 border-2 border-white flex items-center justify-center">
                    <span className="text-white font-serif text-sm font-bold">M</span>
                  </div>
                  <div>
                    <h1 className="text-lg font-serif tracking-tight text-white group-hover:text-zinc-300 transition-colors">
                      MERTON
                    </h1>
                    <p className="text-[8px] text-zinc-500 uppercase tracking-[0.3em] -mt-1">
                      Credit Analytics
                    </p>
                  </div>
                </div>
              </Link>

              {/* Desktop Navigation */}
              <div className="hidden md:flex items-center gap-8">
                <Link href="/">
                  <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500 hover:text-white transition-colors cursor-pointer">
                    Scanner
                  </span>
                </Link>
                <Link href="/dashboard">
                  <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500 hover:text-white transition-colors cursor-pointer">
                    Market
                  </span>
                </Link>
                <Link href="/watchlist">
                  <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500 hover:text-white transition-colors cursor-pointer">
                    Watchlist
                  </span>
                </Link>
                <Link href="/case-studies">
                  <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-zinc-500 hover:text-white transition-colors cursor-pointer">
                    Historical
                  </span>
                </Link>
              </div>
            </nav>
          </div>
        </header>

        {children}
        
        {/* Mobile Navigation*/}
        <MobileNav />
      </body>
    </html>
  )
}