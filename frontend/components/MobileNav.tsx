'use client';

import { Home, BarChart3, Star } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';

export default function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { icon: Home, label: 'Home', href: '/' },
    { icon: BarChart3, label: 'Dashboard', href: '/dashboard' },
    { icon: Star, label: 'Watchlist', href: '/watchlist' },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-800 z-50">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link key={item.href} href={item.href} className="flex-1">
              <motion.div
                whileTap={{ scale: 0.9 }}
                className={`flex flex-col items-center justify-center h-full ${
                  isActive ? 'text-emerald-400' : 'text-zinc-400'
                }`}
              >
                <Icon size={24} />
                <span className="text-xs mt-1">{item.label}</span>
              </motion.div>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}