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
                {/* Active Top Border instead of glow */}
                {isActive && (
                  <div className="absolute top-0 w-full h-[2px] bg-white" />
                )}
                
                <Icon 
                  size={18} 
                  strokeWidth={1.5}
                  className={`mb-1 transition-colors ${isActive ? 'text-white' : 'text-zinc-600 group-hover:text-zinc-400'}`} 
                />
                <span className={`text-[9px] uppercase tracking-widest font-medium ${isActive ? 'text-white' : 'text-zinc-600'}`}>
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