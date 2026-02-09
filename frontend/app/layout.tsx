import './globals.css';
import { Inter, Playfair_Display } from 'next/font/google';
import Link from 'next/link'; // 🆕 Explicitly imported
import MobileNav from '@/components/MobileNav';

const sans = Inter({ subsets: ['latin'], variable: '--font-sans' });
const serif = Playfair_Display({ subsets: ['latin'], variable: '--font-serif' });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable}`}>
      <body className="bg-black text-white min-h-screen font-sans selection:bg-zinc-800 selection:text-white">
        {/* Header - Fixed & Institutional */}
        <header className="border-b border-zinc-900 bg-black sticky top-0 z-50 h-20 flex items-center">
          <div className="container mx-auto px-6 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-6 group">
              {/* Logo Mark */}
              <div className="flex gap-1 items-end h-6">
                <div className="w-1.5 h-6 bg-white" />
                <div className="w-1.5 h-3 bg-zinc-700 group-hover:bg-zinc-500 transition-colors" />
                <div className="w-1.5 h-4 bg-white" />
              </div>
              
              <div className="flex flex-col border-l border-zinc-800 pl-6 h-8 justify-center">
                <h1 className="text-xl font-serif font-medium tracking-[0.15em] text-white uppercase leading-none">
                  Merton
                </h1>
                <span className="text-[8px] font-sans font-medium tracking-[0.3em] text-zinc-500 uppercase mt-1">
                  Credit Analytics
                </span>
              </div>
            </Link>

            {/* Desktop Nav */}
            <nav className="hidden md:flex gap-12 text-[10px] font-bold uppercase tracking-[0.25em] text-zinc-500">
              <Link href="/" className="hover:text-white transition-colors">Scanner</Link>
              <Link href="/dashboard" className="hover:text-white transition-colors">Market</Link>
              <Link href="/watchlist" className="hover:text-white transition-colors">Watchlist</Link>
              <Link href="/case-studies" className="hover:text-white transition-colors">Historical</Link>
            </nav>
          </div>
        </header>

        {children}
        
        <MobileNav />
      </body>
    </html>
  );
}