import './globals.css'
import type { Metadata } from 'next'
import { Source_Serif_4, Public_Sans, IBM_Plex_Mono } from 'next/font/google'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

const serif = Source_Serif_4({
  subsets: ['latin'],
  weight: ['400', '600'],
  variable: '--font-serif',
  display: 'swap',
})
const sans = Public_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
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
    'Does equity-implied distance to default separate firms that subsequently ' +
    'default from comparable firms that do not, and what does that cost in false positives?',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${serif.variable} ${sans.variable} ${mono.variable}`}
    >
      <body>
        <Nav />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  )
}
