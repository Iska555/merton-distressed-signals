'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TickerSearch from '@/components/TickerSearch';
import SkeletonLoader from '@/components/SkeletonLoader';
import SignalCard from '@/components/SignalCard';
import MertonResultsCard from '@/components/MertonResultsCard';
import SensitivityTable from '@/components/SensitivityTable';
import { analyzeTicker, analyzeSensitivity, AnalysisResponse, SensitivityResponse } from '@/lib/api';
import { motion } from 'framer-motion';
import SpreadChart from '@/components/SpreadChart';
import WhatIfSliders from '@/components/WhatIfSliders';
import WatchlistButton from '@/components/WatchlistButton';
import MobileNav from '@/components/MobileNav';

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showSensitivity, setShowSensitivity] = useState(false);

  const handleSearch = async (ticker: string) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    setSensitivity(null);
    setShowSensitivity(false);

    try {
      const result = await analyzeTicker(ticker);
      setAnalysis(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze ticker');
    } finally {
      setLoading(false);
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
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-zinc-800 backdrop-blur-sm bg-black/50 sticky top-0 z-50"
      >
        <div className="container mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
            🎯 Merton Credit Scanner
          </h1>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        {/* Search Section */}
        <div className="mb-12">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center mb-8"
          >
            <h2 className="text-4xl font-bold mb-4">
              Discover Credit Arbitrage Opportunities
            </h2>
            <h3 className="text-zinc-400 text-lg">
              Analyze equity volatility to find mispriced corporate bonds
            </h3>
          </motion.div>

          <TickerSearch onSearch={handleSearch} loading={loading} />
        </div>

        {/* Error State */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-2xl mx-auto bg-red-500/10 border border-red-500/50 rounded-2xl p-6 mb-8"
          >
            <p className="text-red-400 text-center">{error}</p>
          </motion.div>
        )}

        {/* Loading State */}
        {loading && <SkeletonLoader />}

        {/* Results */}
        {analysis && !loading && (
          <div className="max-w-6xl mx-auto space-y-8">
            {/* Company Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <div className="flex items-center justify-center gap-4">
                <h3 className="text-4xl font-bold">{analysis.company.company_name}</h3>
                <WatchlistButton ticker={analysis.company.ticker} />
              </div>
              <p className="text-zinc-400">
                {analysis.company.ticker} • {analysis.company.sector} • {analysis.company.industry}
              </p>
            </motion.div>

            {/* Input Stats Grid */}
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
                  whileHover={{ scale: 1.05 }}
                  className="bg-zinc-900 rounded-2xl p-6 border border-zinc-800"
                >
                  <p className="text-zinc-400 text-sm mb-2">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </motion.div>
              ))}
            </motion.div>

            {/* Merton Results */}
            <MertonResultsCard merton={analysis.merton} E={analysis.E} D={analysis.D} />

            <SpreadChart
              theoSpread={analysis.merton.theo_spread_bps}
              marketSpread={analysis.market_spread_bps}
              volatilitySensitivity={sensitivity?.volatility_sensitivity}
            />

            {/* Signal Card */}
            <SignalCard
              signal={analysis.signal.signal}
              signalStrength={analysis.signal.signal_strength}
              spreadDiff={analysis.signal.spread_diff_bps}
              theoSpread={analysis.merton.theo_spread_bps}
              marketSpread={analysis.market_spread_bps}
            />

            {/* Sensitivity Toggle */}
            <div className="flex justify-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSensitivityToggle}
                className="px-8 py-4 bg-purple-500/20 border border-purple-500/50 rounded-2xl text-purple-400 font-semibold hover:bg-purple-500/30 transition-colors"
              >
                {showSensitivity ? 'Hide' : 'View'} Sensitivity Analysis
              </motion.button>
            </div>

            {/* Sensitivity Table */}
            {showSensitivity && sensitivity && <SensitivityTable sensitivity={sensitivity} />}
          </div>
        )}
      </main>

      <MobileNav />

      {/* Footer */}
      <footer className="border-t border-zinc-800 mt-20 py-8">
        <div className="container mx-auto px-6 text-center text-zinc-500 text-sm">
          <p>Merton Credit Scanner • Built with Next.js, FastAPI, and the Merton Structural Model</p>
        </div>
      </footer>
    </div>
  );
}