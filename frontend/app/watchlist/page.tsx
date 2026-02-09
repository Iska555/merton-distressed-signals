'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Download, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useWatchlist } from '@/hooks/useWatchlist';
import { analyzeTicker, AnalysisResponse } from '@/lib/api';
import WatchlistHeader from '@/components/WatchlistHeader';
import WatchlistItem from '@/components/WatchlistItem';
import EmptyWatchlist from '@/components/EmptyWatchlist';
import MobileNav from '@/components/MobileNav';

export default function WatchlistPage() {
  const { watchlist, isLoading: watchlistLoading, addTicker, removeTicker } = useWatchlist();
  const [dataMap, setDataMap] = useState<Record<string, AnalysisResponse | null>>({});
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});
  const [refreshing, setRefreshing] = useState(false);

  // Fetch data for all tickers
  useEffect(() => {
    const fetchWatchlistData = async () => {
      for (const ticker of watchlist) {
        if (!dataMap[ticker] && !loadingMap[ticker]) {
          setLoadingMap((prev) => ({ ...prev, [ticker]: true }));
          
          try {
            const result = await analyzeTicker(ticker);
            setDataMap((prev) => ({ ...prev, [ticker]: result }));
          } catch (err) {
            console.error(`Failed to fetch ${ticker}:`, err);
            setDataMap((prev) => ({ ...prev, [ticker]: null }));
          } finally {
            setLoadingMap((prev) => ({ ...prev, [ticker]: false }));
          }
        }
      }
    };

    if (!watchlistLoading && watchlist.length > 0) {
      fetchWatchlistData();
    }
  }, [watchlist, watchlistLoading]);

  // Refresh all data
  const handleRefresh = async () => {
    setRefreshing(true);
    setDataMap({});
    setLoadingMap({});
    
    for (const ticker of watchlist) {
      setLoadingMap((prev) => ({ ...prev, [ticker]: true }));
      
      try {
        const result = await analyzeTicker(ticker);
        setDataMap((prev) => ({ ...prev, [ticker]: result }));
      } catch (err) {
        setDataMap((prev) => ({ ...prev, [ticker]: null }));
      } finally {
        setLoadingMap((prev) => ({ ...prev, [ticker]: false }));
      }
    }
    
    setRefreshing(false);
  };

  // Export to CSV
  const handleExport = () => {
    const rows = watchlist.map((ticker) => {
      const data = dataMap[ticker];
      if (!data) return null;
      
      return {
        Ticker: ticker,
        Company: data.company.company_name,
        Signal: data.signal.signal,
        'Theo Spread': data.merton.theo_spread_bps,
        'Market Spread': data.market_spread_bps,
        'Spread Diff': data.signal.spread_diff_bps,
        'Distance to Default': data.merton.distance_to_default,
        Rating: data.estimated_rating,
      };
    }).filter(Boolean);

    if (rows.length === 0) return;

    const headers = Object.keys(rows[0]!);
    const csv = [
      headers.join(','),
      ...rows.map((row) => headers.map((h) => row![h as keyof typeof row]).join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `watchlist-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (watchlistLoading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white pb-20 md:pb-0">
      {/* Header */}
      <header className="border-b border-zinc-800 backdrop-blur-sm bg-black/50 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <ArrowLeft size={24} />
              </motion.button>
            </Link>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
              ⭐ Watchlist
            </h1>
          </div>

          {watchlist.length > 0 && (
            <div className="flex gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleRefresh}
                disabled={refreshing}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
              >
                {refreshing ? 'Refreshing...' : 'Refresh All'}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleExport}
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
              >
                <Download size={16} />
                Export CSV
              </motion.button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12 max-w-6xl">
        <WatchlistHeader onAddTicker={addTicker} count={watchlist.length} />

        {watchlist.length === 0 ? (
          <EmptyWatchlist />
        ) : (
          <motion.div layout className="space-y-4">
            <AnimatePresence mode="popLayout">
              {watchlist.map((ticker, index) => (
                <WatchlistItem
                  key={ticker}
                  ticker={ticker}
                  data={dataMap[ticker] ?? null}
                  loading={loadingMap[ticker] ?? false}
                  onRemove={() => removeTicker(ticker)}
                  index={index}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Info Banner */}
        {watchlist.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-12 bg-blue-500/10 border border-blue-500/30 rounded-2xl p-6 flex items-start gap-4"
          >
            <AlertCircle className="text-blue-400 flex-shrink-0" size={24} />
            <div>
              <h4 className="font-semibold text-white mb-2">Real-Time Monitoring</h4>
              <p className="text-sm text-zinc-400">
                Your watchlist is updated with live data. Strong signals (★★★★★) will pulse to catch your attention. 
                Click "Refresh All" to get the latest credit risk analysis for all tickers.
              </p>
            </div>
          </motion.div>
        )}
      </main>

      <MobileNav />
    </div>
  );
}