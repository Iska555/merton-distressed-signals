'use client';

import { useState, useEffect } from 'react';
import { Star } from 'lucide-react';
import { motion } from 'framer-motion';

interface WatchlistButtonProps {
  ticker: string;
}

export default function WatchlistButton({ ticker }: WatchlistButtonProps) {
  const [isWatched, setIsWatched] = useState(false);

  useEffect(() => {
    const watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
    setIsWatched(watchlist.includes(ticker));
  }, [ticker]);

  const toggleWatchlist = () => {
    const watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
    if (isWatched) {
      const updated = watchlist.filter((t: string) => t !== ticker);
      localStorage.setItem('watchlist', JSON.stringify(updated));
      setIsWatched(false);
    } else {
      const updated = [...watchlist, ticker];
      localStorage.setItem('watchlist', JSON.stringify(updated));
      setIsWatched(true);
    }
  };

  return (
    <motion.button
      whileTap={{ scale: 0.9 }}
      onClick={toggleWatchlist}
      className="group relative"
    >
      <Star 
        size={20} 
        className={`transition-colors ${isWatched ? 'text-white fill-white' : 'text-zinc-600 hover:text-white'}`}
        strokeWidth={1.5}
      />
    </motion.button>
  );
}