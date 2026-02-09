'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { analyzeBatch, BatchAnalysisResponse, AnalysisResponse } from '@/lib/api';
import { TrendingUp, TrendingDown } from 'lucide-react';
import Link from 'next/link';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<BatchAnalysisResponse | null>(null);

  useEffect(() => {
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
      }
    };

    fetchTopSignals();
  }, []);

  const SignalRow = ({ signal, index }: { signal: AnalysisResponse; index: number }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02, x: 10 }}
      className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 hover:border-emerald-500/50 transition-all cursor-pointer"
    >
      <Link href={`/analysis/${signal.company.ticker}`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="font-bold text-white">{signal.company.ticker}</p>
            <p className="text-sm text-zinc-400">{signal.company.company_name}</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-xs text-zinc-500">Theo</p>
              <p className="font-medium text-white">{signal.merton.theo_spread_bps.toFixed(0)} bps</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-zinc-500">Market</p>
              <p className="font-medium text-white">{signal.market_spread_bps.toFixed(0)} bps</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-zinc-500">Diff</p>
              <p className={`font-bold ${signal.signal.spread_diff_bps > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {signal.signal.spread_diff_bps > 0 ? '+' : ''}
                {signal.signal.spread_diff_bps.toFixed(0)} bps
              </p>
            </div>
            <div className="text-2xl">{signal.signal.signal_strength}</div>
          </div>
        </div>
      </Link>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="border-b border-zinc-800 backdrop-blur-sm bg-black/50 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
            📈 Market Dashboard
          </h1>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h2 className="text-3xl font-bold mb-2">
            Daily Credit Signals
          </h2>
          <p className="text-zinc-400">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </motion.div>

        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Short Credit Opportunities */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <TrendingDown className="text-red-400" size={24} />
                <h3 className="text-xl font-bold text-white">Top SHORT CREDIT</h3>
              </div>
              <div className="space-y-3">
                {data.top_short_signals.slice(0, 5).map((signal, idx) => (
                  <SignalRow key={signal.company.ticker} signal={signal} index={idx} />
                ))}
              </div>
            </div>

            {/* Long Credit Opportunities */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="text-emerald-400" size={24} />
                <h3 className="text-xl font-bold text-white">Top LONG CREDIT</h3>
              </div>
              <div className="space-y-3">
                {data.top_long_signals.slice(0, 5).map((signal, idx) => (
                  <SignalRow key={signal.company.ticker} signal={signal} index={idx} />
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}