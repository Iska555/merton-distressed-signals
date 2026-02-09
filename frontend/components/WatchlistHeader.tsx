'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus } from 'lucide-react';

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
    <div className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="relative group">
        <div className="relative flex items-center">
          <Search className="absolute left-4 text-zinc-500 group-focus-within:text-white transition-colors" size={16} />
          
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value.toUpperCase())}
            placeholder="ADD TICKER (E.G. AAPL)"
            className="w-full pl-10 pr-12 py-3 bg-black border border-zinc-800 focus:border-white text-white placeholder-zinc-600 focus:outline-none font-mono text-sm uppercase tracking-widest transition-all rounded-none"
          />
          
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="absolute right-2 p-1.5 bg-zinc-900 hover:bg-white hover:text-black text-zinc-400 transition-all disabled:opacity-0 disabled:pointer-events-none rounded-none"
          >
            <Plus size={16} />
          </button>
        </div>
        
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute -bottom-6 left-0 text-[10px] text-red-500 uppercase tracking-widest"
          >
            {error}
          </motion.p>
        )}
      </form>
      
      <p className="mt-3 text-[10px] text-zinc-600 uppercase tracking-[0.2em]">
        {count === 0 ? 'Portfolio Empty' : `Tracking ${count} ${count === 1 ? 'Asset' : 'Assets'}`}
      </p>
    </div>
  );
}