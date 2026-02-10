'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';

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
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative border border-zinc-800">
        <div className="relative flex">
          <div className="flex items-center justify-center px-6 border-r border-zinc-800 bg-zinc-950">
            <Search className="text-zinc-600" size={18} />
          </div>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter ticker symbol (AAPL, TSLA, MSFT)"
            className="flex-1 px-6 py-5 bg-black text-white placeholder-zinc-600 focus:outline-none text-sm font-mono uppercase tracking-wider"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !ticker.trim()}
            className={`
              px-10 py-5 text-[11px] font-bold uppercase tracking-[0.25em] transition-colors border-l border-zinc-800
              ${loading || !ticker.trim()
                ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed'
                : 'bg-white text-black hover:bg-zinc-200'
              }
            `}
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </form>
    </div>
  );
}