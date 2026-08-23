import './globals.css'
import type { Metadata } from 'next'
import { Newsreader, Archivo, IBM_Plex_Mono } from 'next/font/google'
import Script from 'next/script'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

/**
 * Newsreader for display, Archivo for body, IBM Plex Mono for figures.
 *
 * Source Serif 4 was the previous display face and it is a book face: it sets
 * a page of text well and gives a headline no voice at all. Newsreader has the
 * editorial contrast a masthead needs. Public Sans went with it because its
 * neutrality read as provisional next to real numbers.
 */
const display = Newsreader({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  style: ['normal', 'italic'],
  variable: '--font-display',
  display: 'swap',
})
const sans = Archivo({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-sans',
  display: 'swap',
})
const mono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Distressed Credit Signals',
  description:
    'Most corporate bankruptcies cannot be studied. Whether a failed company ' +
    'leaves a usable record depends on when it failed, and the reason is ' +
    'regulatory rather than economic.',
  manifest: '/manifest.webmanifest',
  icons: {
    icon: [
      { url: '/brand/icon.svg', type: 'image/svg+xml' },
      { url: '/brand/favicon-32.png', type: 'image/png', sizes: '32x32' },
    ],
    apple: [{ url: '/brand/apple-touch-icon.png', sizes: '180x180' }],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
      suppressHydrationWarning
    >
      <body>
        <Script id="restore-theme" strategy="beforeInteractive">
          {`try{if(localStorage.getItem('dcs-theme')==='dark'){document.documentElement.dataset.theme='dark'}}catch{}`}
        </Script>
        <Nav />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  )
}
