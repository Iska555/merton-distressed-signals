'use client';

import { useState, useEffect, Suspense, useCallback } from 'react'; // 🆕 Added useCallback
import { useSearchParams } from 'next/navigation';
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

// 🆕 FIXED HANDLER: 100ms delay prevents the "Analysis Failed" race condition
function SearchParamsHandler({ onSearch }: { onSearch: (ticker: string) => void }) {
  const searchParams = useSearchParams();
  const ticker = searchParams.get('ticker');

  useEffect(() => {
    if (ticker) {
      const timeoutId = setTimeout(() => {
        onSearch(ticker);
      }, 100); // Small delay to ensure hydration
      return () => clearTimeout(timeoutId);
    }
  }, [ticker, onSearch]);

  return null;
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastTicker, setLastTicker] = useState<string>('');
  const [showSensitivity, setShowSensitivity] = useState(false);

  // 🆕 STABILIZED FUNCTION: Wrapped in useCallback to prevent re-render loops
  const handleSearch = useCallback(async (ticker: string) => {
    if (!ticker) return;

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
      console.error("Analysis Error:", err);
      const errorMessage = err.response?.data?.detail || 'Failed to analyze ticker. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []); // Empty dependency array keeps this function stable

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

      <main className="container mx-auto px-6 py-16 max-w-6xl">
        {/* Only show Hero Text if NOT analyzing (prevents layout jump) */}
        {!analysis && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-16"
          >
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-serif tracking-tight mb-4 text-white">
                Structural Credit Analysis
              </h2>
              <p className="text-zinc-500 font-sans tracking-[0.2em] text-xs uppercase max-w-2xl mx-auto leading-relaxed">
                Quantitative arbitrage detection via equity volatility mapping
              </p>
            </div>
          </motion.div>
        )}

        {/* Search Bar Container */}
        <div className={analysis ? "mb-12" : "mb-0"}>
           <TickerSearch onSearch={handleSearch} loading={loading} />
        </div>

        {error && <ErrorState error={error} onRetry={handleRetry} ticker={lastTicker} />}
        {loading && <SkeletonLoader />}

        {analysis && !loading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="space-y-12"
          >
            {/* Ticker Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 260, damping: 20 }}
              className="text-center border-b border-zinc-900 pb-8"
            >
              <div className="flex items-center justify-center gap-4 mb-2">
                <h3 className="text-5xl font-serif text-white tracking-tight">
                  {analysis.company.company_name}
                </h3>
                <WatchlistButton ticker={analysis.company.ticker} />
              </div>
              <p className="text-zinc-500 font-mono text-[10px] uppercase tracking-[0.3em]">
                {analysis.company.ticker} • {analysis.company.sector}
              </p>
            </motion.div>

            {/* Input Stats Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, type: "spring", stiffness: 260, damping: 20 }}
              className="grid grid-cols-2 md:grid-cols-4 border-t border-l border-zinc-800"
            >
              {[
                { label: 'Market Cap', value: formatCurrency(analysis.E) },
                { label: 'Total Debt', value: formatCurrency(analysis.D) },
                { label: 'Equity Vol.', value: `${(analysis.sigma_E * 100).toFixed(1)}%` },
                { label: 'Implied Rating', value: analysis.estimated_rating },
              ].map((stat, idx) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.15 + idx * 0.05, type: "spring", stiffness: 260, damping: 20 }}
                  className="bg-black p-8 border-r border-b border-zinc-800 hover:bg-zinc-950 transition-colors"
                >
                  <p className="text-zinc-500 text-[9px] uppercase tracking-[0.25em] mb-3 font-bold">
                    {stat.label}
                  </p>
                  <p className="text-3xl font-serif text-white">{stat.value}</p>
                </motion.div>
              ))}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, type: "spring", stiffness: 260, damping: 20 }}
            >
              <MertonResultsCard merton={analysis.merton} E={analysis.E} D={analysis.D} />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, type: "spring", stiffness: 260, damping: 20 }}
            >
              <SpreadChart
                theoSpread={analysis.merton.theo_spread_bps}
                marketSpread={analysis.market_spread_bps}
                volatilitySensitivity={sensitivity?.volatility_sensitivity}
              />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, type: "spring", stiffness: 260, damping: 20 }}
            >
              <SignalCard
                signal={analysis.signal.signal}
                signalStrength={analysis.signal.signal_strength}
                spreadDiff={analysis.signal.spread_diff_bps}
                theoSpread={analysis.merton.theo_spread_bps}
                marketSpread={analysis.market_spread_bps}
              />
            </motion.div>

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

            {showSensitivity && sensitivity && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 260, damping: 20 }}
              >
                <SensitivityTable sensitivity={sensitivity} />
              </motion.div>
            )}
          </motion.div>
        )}
      </main>
      
      {/* 🆕 Updated Professional Footer */}
      <footer className="border-t border-zinc-900 py-12 mt-20">
        <div className="container mx-auto px-6 text-center">
          <div className="space-y-2">
            <p className="text-zinc-500 text-xs font-serif tracking-widest">
              MERTON QUANTITATIVE RESEARCH
            </p>
            <p className="text-zinc-700 text-[9px] uppercase tracking-[0.2em]">
              For Institutional Use Only • Not Investment Advice • Data delayed 15m
            </p>
          </div>
        </div>
      </footer>
      
      <MobileNav />
    </div>
  );
}