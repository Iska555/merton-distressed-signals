'use client';

import { Home, BarChart3, Star, BookOpen } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { icon: Home, label: 'Scanner', href: '/' },
    { icon: BarChart3, label: 'Market', href: '/dashboard' },
    { icon: Star, label: 'Watchlist', href: '/watchlist' },
    { icon: BookOpen, label: 'Cases', href: '/case-studies' },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-black border-t border-zinc-800 z-50">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link key={item.href} href={item.href} className="flex-1 group">
              <div className="flex flex-col items-center justify-center h-full relative">
                <Icon 
                  size={18} 
                  strokeWidth={1.5}
                  className={`mb-1 transition-all ${
                    isActive 
                      ? 'text-white drop-shadow-[0_0_6px_rgba(255,255,255,0.5)]' 
                      : 'text-zinc-600 group-hover:text-zinc-400'
                  }`} 
                />
                <span className={`text-[9px] uppercase tracking-widest font-medium transition-all ${
                  isActive 
                    ? 'text-white drop-shadow-[0_0_6px_rgba(255,255,255,0.5)]' 
                    : 'text-zinc-600'
                }`}>
                  {item.label}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}