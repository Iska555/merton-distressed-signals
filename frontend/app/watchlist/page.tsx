'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, RefreshCw, AlertCircle } from 'lucide-react';
import Link from 'next/link'; // 🆕 Added Link import
import { useWatchlist } from '@/hooks/useWatchlist';
import { analyzeTicker, AnalysisResponse } from '@/lib/api';
import WatchlistHeader from '@/components/WatchlistHeader';
import WatchlistItem from '@/components/WatchlistItem';
import EmptyWatchlist from '@/components/EmptyWatchlist';
import MobileNav from '@/components/MobileNav';

export default function WatchlistPage() {
  const { watchlist, isLoading, addTicker, removeTicker } = useWatchlist();
  const [dataMap, setDataMap] = useState<Record<string, AnalysisResponse | null>>({});
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const fetchWatchlistData = async () => {
      for (const ticker of watchlist) {
        if (!dataMap[ticker] && !loadingMap[ticker]) {
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
      }
    };
    if (!isLoading && watchlist.length > 0) fetchWatchlistData();
  }, [watchlist, isLoading]);

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

  if (isLoading) {
    return <div className="min-h-screen bg-black flex items-center justify-center"><div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full"/></div>;
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <main className="container mx-auto px-6 py-12 max-w-6xl">
        {/* Unified Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 border-b border-zinc-900 pb-8 gap-8">
           <div className="w-full md:w-auto">
             <h2 className="text-4xl md:text-5xl font-serif text-white tracking-tight mb-6">
               My Watchlist
             </h2>
             <WatchlistHeader onAddTicker={addTicker} count={watchlist.length} />
           </div>
           
           {watchlist.length > 0 && (
             <div className="flex gap-8 text-[10px] uppercase tracking-[0.25em] text-zinc-500 font-bold">
                <button onClick={handleRefresh} disabled={refreshing} className="hover:text-white flex items-center gap-2 transition-colors">
                  <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} /> Refresh
                </button>
                <button onClick={handleExport} className="hover:text-white flex items-center gap-2 transition-colors">
                  <Download size={12} /> Export CSV
                </button>
             </div>
           )}
        </div>

        {watchlist.length === 0 ? (
          <EmptyWatchlist />
        ) : (
          <motion.div layout className="border-t border-zinc-900">
            <AnimatePresence mode="popLayout">
              {watchlist.map((ticker, index) => (
                // 🆕 Wrapped Item in Link for Click-to-Scan functionality
                <Link key={ticker} href={`/?ticker=${ticker}`} className="block">
                  <WatchlistItem
                    ticker={ticker}
                    data={dataMap[ticker] ?? null}
                    loading={loadingMap[ticker] ?? false}
                    onRemove={() => removeTicker(ticker)}
                    index={index}
                  />
                </Link>
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
            className="mt-12 p-6 border-t border-zinc-900 flex items-start gap-4"
          >
            <AlertCircle className="text-zinc-600 flex-shrink-0" size={16} />
            <div>
              <h4 className="font-serif text-sm text-zinc-300 mb-1">Real-Time Monitoring</h4>
              <p className="text-[10px] text-zinc-600 uppercase tracking-wide leading-relaxed">
                Strong signals will pulse to catch your attention. Data refreshes based on real-time equity volatility inputs.
              </p>
            </div>
          </motion.div>
        )}
      </main>
      <MobileNav />
    </div>
  );
}