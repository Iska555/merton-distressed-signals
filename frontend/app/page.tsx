'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import TickerSearch from '@/components/TickerSearch';
import SkeletonLoader from '@/components/SkeletonLoader';
import SignalCard from '@/components/SignalCard';
import MertonResultsCard from '@/components/MertonResultsCard';
import SensitivityTable from '@/components/SensitivityTable';
import SpreadChart from '@/components/SpreadChart';
import WatchlistButton from '@/components/WatchlistButton';
import MobileNav from '@/components/MobileNav';
import ErrorState from '@/components/ErrorState';
import { analyzeTicker, analyzeSensitivity, AnalysisResponse, SensitivityResponse } from '@/lib/api';
import { motion } from 'framer-motion';

function SearchParamsHandler({ onSearch }: { onSearch: (ticker: string) => void }) {
  const searchParams = useSearchParams();
  useEffect(() => {
    const ticker = searchParams.get('ticker');
    if (ticker) onSearch(ticker);
  }, [searchParams, onSearch]);
  return null;
}

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastTicker, setLastTicker] = useState<string>('');
  const [showSensitivity, setShowSensitivity] = useState(false);

  const handleSearch = async (ticker: string) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    setSensitivity(null);
    setShowSensitivity(false);
    setLastTicker(ticker);

    try {
      const result = await analyzeTicker(ticker);
      setAnalysis(result);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to analyze ticker. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => lastTicker && handleSearch(lastTicker);

  const handleSensitivityToggle = async () => {
    if (!analysis) return;
    if (!sensitivity) {
      try {
        const result = await analyzeSensitivity(analysis.company.ticker);
        setSensitivity(result);
        setShowSensitivity(true);
      } catch (err) {
        setError('Failed to load sensitivity analysis');
      }
    } else {
      setShowSensitivity(!showSensitivity);
    }
  };

  const formatCurrency = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    return `$${(value / 1e6).toFixed(2)}M`;
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <Suspense fallback={null}>
        <SearchParamsHandler onSearch={handleSearch} />
      </Suspense>

      {/* HEADER REMOVED - Handled by layout.tsx */}

      <main className="container mx-auto px-6 py-16">
        <div className="mb-16">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl md:text-5xl font-serif tracking-tight mb-4 text-white">
              Structural Credit Analysis
            </h2>
            <p className="text-zinc-500 font-sans tracking-[0.2em] text-xs uppercase max-w-2xl mx-auto leading-relaxed">
              Quantitative arbitrage detection via equity volatility mapping
            </p>
          </motion.div>

          {/* Search Component (Updated styles below) */}
          <TickerSearch onSearch={handleSearch} loading={loading} />
        </div>

        {error && <ErrorState error={error} onRetry={handleRetry} ticker={lastTicker} />}
        {loading && <SkeletonLoader />}

        {analysis && !loading && (
          <div className="max-w-6xl mx-auto space-y-12">
            {/* Ticker Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center border-b border-zinc-900 pb-8"
            >
              <div className="flex items-center justify-center gap-4 mb-2">
                <h3 className="text-5xl font-serif text-white tracking-tight">{analysis.company.company_name}</h3>
                <WatchlistButton ticker={analysis.company.ticker} />
              </div>
              <p className="text-zinc-500 font-mono text-[10px] uppercase tracking-[0.3em]">
                {analysis.company.ticker} • {analysis.company.sector}
              </p>
            </motion.div>

            {/* Input Stats Grid - Sharp & Serif */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="grid grid-cols-2 md:grid-cols-4 border-t border-l border-zinc-800"
            >
              {[
                { label: 'Market Cap', value: formatCurrency(analysis.E) },
                { label: 'Total Debt', value: formatCurrency(analysis.D) },
                { label: 'Equity Vol.', value: `${(analysis.sigma_E * 100).toFixed(1)}%` },
                { label: 'Implied Rating', value: analysis.estimated_rating },
              ].map((stat, idx) => (
                <div
                  key={stat.label}
                  className="bg-black p-8 border-r border-b border-zinc-800 hover:bg-zinc-950 transition-colors"
                >
                  <p className="text-zinc-500 text-[9px] uppercase tracking-[0.25em] mb-3 font-bold">{stat.label}</p>
                  <p className="text-3xl font-serif text-white">{stat.value}</p>
                </div>
              ))}
            </motion.div>

            <MertonResultsCard merton={analysis.merton} E={analysis.E} D={analysis.D} />
            
            <SpreadChart
              theoSpread={analysis.merton.theo_spread_bps}
              marketSpread={analysis.market_spread_bps}
              volatilitySensitivity={sensitivity?.volatility_sensitivity}
            />
            
            <SignalCard
              signal={analysis.signal.signal}
              signalStrength={analysis.signal.signal_strength}
              spreadDiff={analysis.signal.spread_diff_bps}
              theoSpread={analysis.merton.theo_spread_bps}
              marketSpread={analysis.market_spread_bps}
            />

            <div className="flex justify-center pt-8 border-t border-zinc-900">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSensitivityToggle}
                className="px-8 py-4 bg-white text-black text-[11px] font-bold uppercase tracking-[0.25em] hover:bg-zinc-200 transition-colors"
              >
                {showSensitivity ? 'Hide' : 'Generate'} Sensitivity Matrix
              </motion.button>
            </div>

            {showSensitivity && sensitivity && <SensitivityTable sensitivity={sensitivity} />}
          </div>
        )}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-zinc-900 py-12 mt-20">
        <div className="container mx-auto px-6 text-center">
           <p className="text-zinc-600 text-[10px] uppercase tracking-[0.4em]">Merton Analytics • Wall St. Grade Models</p>
        </div>
      </footer>
      <MobileNav />
    </div>
  );
}