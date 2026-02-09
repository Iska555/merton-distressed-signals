'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { analyzeBatch, BatchAnalysisResponse, AnalysisResponse } from '@/lib/api';
import { TrendingUp, TrendingDown, RefreshCw, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import MobileNav from '@/components/MobileNav';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<BatchAnalysisResponse | null>(null);

  const fetchTopSignals = async () => {
    try {
      const tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
        'F', 'GM', 'BAC', 'JPM', 'C', 'WFC', 'GS', 'MS',
      ];
      const result = await analyzeBatch(tickers);
      setData(result);
    } catch (err) {
      console.error('Failed to fetch signals:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTopSignals();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchTopSignals();
  };

  const SignalRow = ({ signal, index }: { signal: AnalysisResponse; index: number }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02, x: 8 }}
      className="bg-zinc-900 border border-zinc-800 rounded-none p-4 hover:border-white transition-all cursor-pointer mb-3 border-l-2 border-l-transparent hover:border-l-white"
    >
      <Link href={`/?ticker=${signal.company.ticker}`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="font-serif font-bold text-white text-lg tracking-wider">{signal.company.ticker}</p>
            <p className="text-[10px] text-zinc-500 uppercase tracking-widest truncate max-w-[120px] md:max-w-none">
              {signal.company.company_name}
            </p>
          </div>
          <div className="flex items-center gap-4 md:gap-8">
            <div className="text-right hidden sm:block">
              <p className="text-[9px] text-zinc-600 uppercase tracking-widest">Market</p>
              <p className="font-serif font-medium text-white">{signal.market_spread_bps.toFixed(0)}</p>
            </div>
            <div className="text-right">
              <p className="text-[9px] text-zinc-600 uppercase tracking-widest">Spread Diff</p>
              <p className={`font-serif font-bold ${signal.signal.spread_diff_bps > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {signal.signal.spread_diff_bps > 0 ? '+' : ''}{signal.signal.spread_diff_bps.toFixed(0)}
              </p>
            </div>
            <div className="text-xl w-8 text-center text-white font-serif">{signal.signal.signal_strength}</div>
          </div>
        </div>
      </Link>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full"></div>
          <p className="text-zinc-500 text-[10px] uppercase tracking-widest animate-pulse">Scanning Credit Markets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <main className="container mx-auto px-6 py-12 max-w-6xl">
        {/* Added a local title since header is gone, for context */}
        <div className="flex justify-between items-end mb-12 border-b border-zinc-900 pb-6">
           <div>
             <h2 className="text-3xl font-serif text-white tracking-wide mb-2">Market Dashboard</h2>
             <p className="text-[10px] text-zinc-500 uppercase tracking-[0.2em]">Live Credit Opportunities</p>
           </div>
           <button 
             onClick={handleRefresh}
             disabled={refreshing}
             className="text-[10px] uppercase tracking-widest text-zinc-500 hover:text-white flex items-center gap-2 transition-colors"
           >
             <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
             {refreshing ? 'Scanning...' : 'Refresh Data'}
           </button>
        </div>

        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Short Signals */}
            <section>
              <div className="flex items-center gap-2 mb-6 border-b border-zinc-900 pb-2">
                <TrendingDown className="text-zinc-500" size={16} />
                <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-400">Overvalued Credit (Short)</h3>
              </div>
              <AnimatePresence>
                {data.top_short_signals.map((signal, idx) => (
                  <SignalRow key={signal.company.ticker} signal={signal} index={idx} />
                ))}
              </AnimatePresence>
            </section>

            {/* Long Signals */}
            <section>
              <div className="flex items-center gap-2 mb-6 border-b border-zinc-900 pb-2">
                <TrendingUp className="text-zinc-500" size={16} />
                <h3 className="text-sm font-bold uppercase tracking-widest text-zinc-400">Undervalued Credit (Long)</h3>
              </div>
              <AnimatePresence>
                {data.top_long_signals.map((signal, idx) => (
                  <SignalRow key={signal.company.ticker} signal={signal} index={idx} />
                ))}
              </AnimatePresence>
            </section>
          </div>
        )}
      </main>
      
      {/* Kept MobileNav to ensure safe fallback, though Layout handles it */}
      <MobileNav />
    </div>
  );
}