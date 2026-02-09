'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';

interface TickerSearchProps {
  onSearch: (ticker: string) => void;
  loading?: boolean;
}

export default function TickerSearch({ onSearch, loading = false }: TickerSearchProps) {
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onSearch(ticker.trim().toUpperCase());
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-2xl mx-auto"
    >
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter ticker symbol (e.g., AAPL, TSLA)"
            className="w-full px-6 py-4 bg-zinc-900 border border-zinc-800 rounded-2xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-lg"
            disabled={loading}
          />
          <Search className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500" size={24} />
        </div>
        
        <motion.button
          type="submit"
          disabled={loading || !ticker.trim()}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            mt-4 w-full px-6 py-4 rounded-2xl font-semibold text-lg transition-all
            ${loading || !ticker.trim()
              ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:shadow-lg hover:shadow-emerald-500/50'
            }
          `}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing...
            </span>
          ) : (
            'Analyze Credit Risk'
          )}
        </motion.button>
      </form>
    </motion.div>
  );
}