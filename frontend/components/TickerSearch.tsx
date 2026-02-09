'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';

interface TickerSearchProps {
  onSearch: (ticker: string) => void;
  loading: boolean;
}

export default function TickerSearch({ onSearch, loading }: TickerSearchProps) {
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onSearch(ticker.toUpperCase());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-xl mx-auto">
      <div className="relative group">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="ENTER TICKER (E.G. AAPL)"
          className="w-full bg-black border border-zinc-700 text-white px-6 py-5 pl-14 
                     focus:outline-none focus:border-white transition-colors
                     placeholder:text-zinc-600 font-mono text-lg uppercase tracking-widest rounded-none"
        />
        <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-white transition-colors" size={20} />
      </div>
      
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        type="submit"
        disabled={loading || !ticker}
        className="w-full mt-4 bg-white text-black py-4 font-bold uppercase tracking-[0.25em] text-xs
                   hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all rounded-none"
      >
        {loading ? 'Analyzing Structure...' : 'Run Credit Model'}
      </motion.button>
    </form>
  );
}