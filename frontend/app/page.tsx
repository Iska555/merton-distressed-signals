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

// Child component to handle deep-linked ticker searches
function SearchParamsHandler({ onSearch }: { onSearch: (ticker: string) => void }) {
  const searchParams = useSearchParams();

  useEffect(() => {
    const ticker = searchParams.get('ticker');
    if (ticker) {
      onSearch(ticker);
    }
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

  const handleRetry = () => {
    if (lastTicker) {
      handleSearch(lastTicker);
    }
  };

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
    <div className="min-h-screen bg-black text-white pb-20 md:pb-0">
      <Suspense fallback={null}>
        <SearchParamsHandler onSearch={handleSearch} />
      </Suspense>

      {/* 🆕 Institutional Blackstone-Style Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-zinc-800 bg-black sticky top-0 z-50 py-6"
      >
        <div className="container mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Geometric Structure Mark */}
            <div className="flex gap-1 items-end h-8">
              <div className="w-2 h-8 bg-white" />
              <div className="w-2 h-4 bg-zinc-600" />
              <div className="w-2 h-6 bg-white" />
            </div>
            
            <div className="flex flex-col border-l border-zinc-700 pl-6">
              <h1 className="text-2xl font-serif font-medium tracking-[0.15em] text-white uppercase leading-none">
                Merton
              </h1>
              <span className="text-[9px] font-sans font-light tracking-[0.4em] text-zinc-500 uppercase mt-2">
                Credit Signal Generator
              </span>
            </div>
          </div>

          <nav className="hidden md:flex gap-8 text-[11px] font-medium uppercase tracking-widest text-zinc-400">
            <Link href="/" className="hover:text-white transition-colors">Scanner</Link>
            <Link href="/dashboard" className="hover:text-white transition-colors">Market</Link>
            <Link href="/watchlist" className="hover:text-white transition-colors">Watchlist</Link>
          </nav>
        </div>
      </motion.header>

      <main className="container mx-auto px-6 py-12">
        <div className="mb-12">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl md:text-5xl font-serif tracking-tight mb-4">
              Structural Credit Analysis
            </h2>
            <p className="text-zinc-500 font-sans tracking-wide text-lg max-w-2xl mx-auto uppercase text-[12px]">
              Quantitative arbitrage detection via equity volatility mapping
            </p>
          </motion.div>

          <TickerSearch onSearch={handleSearch} loading={loading} />
        </div>

        {error && <ErrorState error={error} onRetry={handleRetry} ticker={lastTicker} />}
        {loading && <SkeletonLoader />}

        {analysis && !loading && (
          <div className="max-w-6xl mx-auto space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <div className="flex items-center justify-center gap-4 mb-2">
                <h3 className="text-4xl font-serif uppercase tracking-wider">{analysis.company.company_name}</h3>
                <WatchlistButton ticker={analysis.company.ticker} />
              </div>
              <p className="text-zinc-500 font-mono text-xs uppercase tracking-[0.2em]">
                {analysis.company.ticker} • {analysis.company.sector} • {analysis.company.industry}
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-4"
            >
              {[
                { label: 'Market Cap', value: formatCurrency(analysis.E) },
                { label: 'Total Debt', value: formatCurrency(analysis.D) },
                { label: 'Equity Volatility', value: `${(analysis.sigma_E * 100).toFixed(1)}%` },
                { label: 'Credit Rating', value: analysis.estimated_rating },
              ].map((stat, idx) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1 + idx * 0.05 }}
                  className="bg-zinc-950 rounded-none p-6 border border-zinc-900"
                  style={{ minHeight: '108px' }}
                >
                  <p className="text-zinc-600 text-[10px] uppercase tracking-[0.2em] mb-2 font-bold">{stat.label}</p>
                  <p className="text-2xl font-serif">{stat.value}</p>
                </motion.div>
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

            <div className="flex justify-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSensitivityToggle}
                className="px-8 py-4 bg-zinc-900 border border-zinc-800 rounded-none text-zinc-400 text-xs font-bold uppercase tracking-widest hover:bg-zinc-800 transition-colors"
              >
                {showSensitivity ? 'Hide' : 'Generate'} Full Sensitivity Matrix
              </motion.button>
            </div>

            {showSensitivity && sensitivity && <SensitivityTable sensitivity={sensitivity} />}
          </div>
        )}

        <div className="text-center py-24 mt-20 border-t border-zinc-900">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <p className="text-zinc-600 text-[10px] uppercase tracking-[0.3em] mb-8 max-w-md mx-auto leading-loose">
              Historical validation: Model performance during institutional insolvency events
            </p>
            <Link href="/case-studies">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-10 py-5 bg-white text-black text-[11px] font-bold uppercase tracking-[0.3em] transition-all"
              >
                Access Case Studies
              </motion.button>
            </Link>
          </motion.div>
        </div>
      </main>

      <footer className="border-t border-zinc-900 py-12">
        <div className="container mx-auto px-6 text-center text-zinc-700 text-[10px] uppercase tracking-[0.4em]">
          <p>© 2026 Merton quantitative framework • Proprietary credit analytics</p>
        </div>
      </footer>
      <MobileNav />
    </div>
  );
}