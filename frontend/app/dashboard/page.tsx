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
      className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 hover:border-emerald-500/50 transition-all cursor-pointer mb-3"
    >
      <Link href={`/?ticker=${signal.company.ticker}`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="font-bold text-white text-lg">{signal.company.ticker}</p>
            <p className="text-xs text-zinc-500 truncate max-w-[120px] md:max-w-none">
              {signal.company.company_name}
            </p>
          </div>
          <div className="flex items-center gap-4 md:gap-8">
            <div className="text-right hidden sm:block">
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Market</p>
              <p className="font-medium text-white">{signal.market_spread_bps.toFixed(0)}</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Spread Diff</p>
              <p className={`font-bold ${signal.signal.spread_diff_bps > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {signal.signal.spread_diff_bps > 0 ? '+' : ''}{signal.signal.spread_diff_bps.toFixed(0)}
              </p>
            </div>
            <div className="text-2xl w-8 text-center">{signal.signal.signal_strength}</div>
          </div>
        </div>
      </Link>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
          <p className="text-zinc-500 text-sm animate-pulse">Scanning Credit Markets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white pb-24 md:pb-12">
      {/* Header matching Watchlist style */}
      <header className="border-b border-zinc-800 backdrop-blur-sm bg-black/50 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="p-2 hover:bg-zinc-800 rounded-lg transition-colors">
                <ArrowLeft size={24} />
              </motion.button>
            </Link>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
              📈 Market Dashboard
            </h1>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Scanning...' : 'Refresh'}
          </motion.button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 max-w-6xl">
        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Short Signals */}
            <section>
              <div className="flex items-center gap-2 mb-6">
                <div className="p-2 bg-red-500/20 rounded-lg"><TrendingDown className="text-red-400" size={20} /></div>
                <h3 className="text-xl font-bold">Overvalued Credit (Short)</h3>
              </div>
              <AnimatePresence>
                {data.top_short_signals.map((signal, idx) => (
                  <SignalRow key={signal.company.ticker} signal={signal} index={idx} />
                ))}
              </AnimatePresence>
            </section>

            {/* Long Signals */}
            <section>
              <div className="flex items-center gap-2 mb-6">
                <div className="p-2 bg-emerald-500/20 rounded-lg"><TrendingUp className="text-emerald-400" size={20} /></div>
                <h3 className="text-xl font-bold">Undervalued Credit (Long)</h3>
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

      <MobileNav />
    </div>
  );
}