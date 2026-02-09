'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus, Star } from 'lucide-react';

interface WatchlistHeaderProps {
  onAddTicker: (ticker: string) => boolean;
  count: number;
}

export default function WatchlistHeader({ onAddTicker, count }: WatchlistHeaderProps) {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const success = onAddTicker(inputValue);
    
    if (success) {
      setInputValue('');
      setError('');
    } else {
      setError('Already in watchlist or invalid ticker');
      setTimeout(() => setError(''), 2000);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8"
    >
      {/* Title */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
            <Star className="text-yellow-400" size={32} />
            My Watchlist
          </h1>
          <p className="text-zinc-400">
            {count === 0 ? 'No tickers saved yet' : `Tracking ${count} ${count === 1 ? 'ticker' : 'tickers'}`}
          </p>
        </div>
      </div>

      {/* Quick Add Bar */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={20} />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value.toUpperCase())}
            placeholder="Add ticker to watchlist (e.g., AAPL)"
            className="w-full pl-12 pr-12 py-4 bg-zinc-900 border border-zinc-800 rounded-2xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
          <motion.button
            type="submit"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-emerald-500 hover:bg-emerald-600 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!inputValue.trim()}
          >
            <Plus className="text-white" size={20} />
          </motion.button>
        </div>
        
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-sm text-red-400"
          >
            {error}
          </motion.p>
        )}
      </form>
    </motion.div>
  );
}