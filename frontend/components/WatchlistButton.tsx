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
      // Remove from watchlist
      const updated = watchlist.filter((t: string) => t !== ticker);
      localStorage.setItem('watchlist', JSON.stringify(updated));
      setIsWatched(false);
    } else {
      // Add to watchlist
      const updated = [...watchlist, ticker];
      localStorage.setItem('watchlist', JSON.stringify(updated));
      setIsWatched(true);
    }
  };

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={toggleWatchlist}
      className={`p-2 rounded-full transition-colors ${
        isWatched
          ? 'bg-yellow-500/20 text-yellow-400'
          : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
      }`}
    >
      <Star size={20} fill={isWatched ? 'currentColor' : 'none'} />
    </motion.button>
  );
}