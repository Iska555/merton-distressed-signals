'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { analyzeBatch, BatchAnalysisResponse, AnalysisResponse } from '@/lib/api';
import { TrendingUp, TrendingDown, RefreshCw, Clock } from 'lucide-react';
import Link from 'next/link';
import MobileNav from '@/components/MobileNav';

const CACHE_KEY = 'market_dashboard_data';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

interface CachedData {
  data: BatchAnalysisResponse;
  timestamp: number;
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<BatchAnalysisResponse | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchTopSignals = async (forceRefresh = false) => {
    try {
      // Check cache first (unless force refresh)
      if (!forceRefresh) {
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const cachedData: CachedData = JSON.parse(cached);
          const age = Date.now() - cachedData.timestamp;
          
          // Use cache if less than 24 hours old
          if (age < CACHE_DURATION) {
            setData(cachedData.data);
            setLastUpdated(new Date(cachedData.timestamp));
            setLoading(false);
            setRefreshing(false);
            return;
          }
        }
      }

      // Fetch fresh data
      const tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
        'F', 'GM', 'BAC', 'JPM', 'C', 'WFC', 'GS', 'MS',
      ];
      const result = await analyzeBatch(tickers);
      
      // Cache the result
      const cacheData: CachedData = {
        data: result,
        timestamp: Date.now(),
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
      
      setData(result);
      setLastUpdated(new Date());
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
    fetchTopSignals(true); // Force refresh
  };

  const formatLastUpdated = () => {
    if (!lastUpdated) return '';
    
    const now = new Date();
    const diff = now.getTime() - lastUpdated.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours === 0) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else {
      return lastUpdated.toLocaleDateString();
    }
  };

  const SignalRow = ({ signal, index }: { signal: AnalysisResponse; index: number }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, type: "spring", stiffness: 260, damping: 20 }}
      whileHover={{ scale: 1.01, x: 4 }}
      className="bg-zinc-900 border border-zinc-800 rounded-none p-5 hover:border-white transition-all cursor-pointer mb-3 border-l-2 border-l-transparent hover:border-l-white group"
    >
      <Link href={`/?ticker=${signal.company.ticker}`}>
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0 pr-4">
            <div className="flex items-baseline gap-3">
              <p className="font-serif font-bold text-white text-xl tracking-wider group-hover:text-emerald-400 transition-colors">
                {signal.company.ticker}
              </p>
              <p className="text-[10px] text-zinc-500 uppercase tracking-widest truncate hidden sm:block">
                {signal.company.company_name}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-8 md:gap-12">
            <div className="text-right hidden md:block w-20">
              <p className="text-[9px] text-zinc-600 uppercase tracking-widest mb-0.5">Market</p>
              <p className="font-serif font-medium text-white text-lg">{signal.market_spread_bps.toFixed(0)}</p>
            </div>
            
            <div className="text-right w-24">
              <p className="text-[9px] text-zinc-600 uppercase tracking-widest mb-0.5">Spread Diff</p>
              <p className={`font-serif font-bold text-lg ${signal.signal.spread_diff_bps > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {signal.signal.spread_diff_bps > 0 ? '+' : ''}{signal.signal.spread_diff_bps.toFixed(0)}
              </p>
            </div>
            
            <div className="text-lg text-white font-serif tracking-widest min-w-[100px] text-right">
              {signal.signal.signal_strength}
            </div>
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
          <p className="text-zinc-500 text-[10px] uppercase tracking-widest animate-pulse">
            Scanning Credit Markets...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <main className="container mx-auto px-6 md:px-12 py-12 max-w-[1600px]">
        
        {/* Header with Last Updated */}
        <div className="flex justify-between items-end mb-16 border-b border-zinc-900 pb-6">
          <div>
            <h2 className="text-4xl font-serif text-white tracking-tight mb-2">Market Dashboard</h2>
            <p className="text-xs text-zinc-500 uppercase tracking-[0.25em]">
              Live Credit Opportunities & Volatility Arbitrage
            </p>
            {lastUpdated && (
              <div className="flex items-center gap-2 mt-3">
                <Clock size={12} className="text-zinc-600" />
                <p className="text-[10px] text-zinc-600 uppercase tracking-widest font-mono">
                  Last updated: {formatLastUpdated()}
                </p>
              </div>
            )}
          </div>
          
          <button 
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-[10px] uppercase tracking-widest text-zinc-500 hover:text-white flex items-center gap-2 transition-colors border border-zinc-800 px-4 py-2 hover:bg-zinc-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Scanning...' : 'Refresh Now'}
          </button>
        </div>

        {data && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-20">
            {/* Short Signals */}
            <section>
              <div className="flex items-center gap-3 mb-8 border-b border-zinc-800 pb-4">
                <div className="p-1.5 bg-red-900/20 rounded-none border border-red-900/30">
                  <TrendingDown className="text-red-500" size={18} />
                </div>
                <div>
                  <h3 className="text-lg font-serif font-medium text-white">Overvalued Credit (Short)</h3>
                  <p className="text-[9px] text-zinc-500 uppercase tracking-widest">Market spread too low vs. Model risk</p>
                </div>
              </div>
              <div className="space-y-1">
                <AnimatePresence>
                  {data.top_short_signals.map((signal, idx) => (
                    <SignalRow key={signal.company.ticker} signal={signal} index={idx} />
                  ))}
                </AnimatePresence>
              </div>
            </section>

            {/* Long Signals */}
            <section>
              <div className="flex items-center gap-3 mb-8 border-b border-zinc-800 pb-4">
                <div className="p-1.5 bg-emerald-900/20 rounded-none border border-emerald-900/30">
                  <TrendingUp className="text-emerald-500" size={18} />
                </div>
                <div>
                  <h3 className="text-lg font-serif font-medium text-white">Undervalued Credit (Long)</h3>
                  <p className="text-[9px] text-zinc-500 uppercase tracking-widest">Market spread too high vs. Model risk</p>
                </div>
              </div>
              <div className="space-y-1">
                <AnimatePresence>
                  {data.top_long_signals.map((signal, idx) => (
                    <SignalRow key={signal.company.ticker} signal={signal} index={idx} />
                  ))}
                </AnimatePresence>
              </div>
            </section>
          </div>
        )}

        {/* Cache Notice */}
        <div className="mt-16 border-t border-zinc-900 pt-8 text-center">
          <p className="text-[10px] text-zinc-600 uppercase tracking-widest font-mono">
            Data cached for 24 hours • Click "Refresh Now" for latest market scan
          </p>
        </div>
      </main>
      
      <MobileNav />
    </div>
  );
}