'use client';

import { Home, BarChart3, Star, BookOpen } from 'lucide-react'; // 🆕 Added BookOpen
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';

export default function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { icon: Home, label: 'Home', href: '/' },
    { icon: BarChart3, label: 'Dashboard', href: '/dashboard' },
    { icon: Star, label: 'Watchlist', href: '/watchlist' },
    { icon: BookOpen, label: 'Cases', href: '/case-studies' }, // 🆕 Added Case Studies
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-black/80 backdrop-blur-xl border-t border-zinc-800 z-50">
      <div className="flex justify-around items-center h-20 pb-4"> {/* Increased height for better spacing */}
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link key={item.href} href={item.href} className="flex-1">
              <motion.div
                whileTap={{ scale: 0.9 }}
                className={`flex flex-col items-center justify-center h-full transition-colors duration-200 ${
                  isActive ? 'text-emerald-400' : 'text-zinc-500'
                }`}
              >
                {/* Active Indicator Bar */}
                {isActive && (
                  <motion.div 
                    layoutId="activeTab"
                    className="absolute top-0 w-8 h-1 bg-emerald-400 rounded-b-full shadow-[0_0_10px_rgba(52,211,153,0.5)]"
                  />
                )}
                
                <Icon size={22} className={isActive ? 'drop-shadow-[0_0_8px_rgba(52,211,153,0.5)]' : ''} />
                <span className={`text-[10px] mt-1.5 font-medium ${isActive ? 'text-emerald-400' : 'text-zinc-500'}`}>
                  {item.label}
                </span>
              </motion.div>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}