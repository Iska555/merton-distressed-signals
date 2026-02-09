'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, Bell, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import CountUp from 'react-countup';
import { AnalysisResponse } from '@/lib/api';

interface WatchlistItemProps {
  ticker: string;
  data: AnalysisResponse | null;
  loading: boolean;
  onRemove: () => void;
  index: number;
}

export default function WatchlistItem({
  ticker,
  data,
  loading,
  onRemove,
  index,
}: WatchlistItemProps) {
  const [showActions, setShowActions] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  // Generate mock sparkline data (in production, this would come from historical API)
  const sparklineData = Array.from({ length: 7 }, (_, i) => ({
    day: i,
    dd: data ? data.merton.distance_to_default + (Math.random() - 0.5) * 0.5 : 0,
  }));

  const isLong = data && data.signal.spread_diff_bps < -75;
  const isShort = data && data.signal.spread_diff_bps > 75;
  const isStrong = data && Math.abs(data.signal.spread_diff_bps) > 150;

  const SignalIcon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;
  const signalColor = isLong ? 'text-emerald-400' : isShort ? 'text-red-400' : 'text-zinc-400';
  const signalBg = isLong
    ? 'bg-emerald-500/20 border-emerald-500/50'
    : isShort
    ? 'bg-red-500/20 border-red-500/50'
    : 'bg-zinc-700/20 border-zinc-600/50';

  // Skeleton loader
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 animate-pulse"
      >
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 bg-zinc-800 rounded-xl"></div>
          <div className="flex-1">
            <div className="h-4 bg-zinc-800 rounded w-1/3 mb-2"></div>
            <div className="h-3 bg-zinc-800 rounded w-1/2"></div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Error state
  if (!data) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ delay: index * 0.05 }}
        layout
        className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4"
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="font-bold text-white">{ticker}</p>
            <p className="text-sm text-red-400">Failed to load data</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onRemove}
            className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
          >
            <Trash2 className="text-red-400" size={18} />
          </motion.button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, height: 0 }}
      transition={{ delay: index * 0.05 }}
      layout
      whileHover={{ x: 5 }}
      whileTap={{ scale: 0.98 }}
      onHoverStart={() => setShowActions(true)}
      onHoverEnd={() => setShowActions(false)}
      className={`
        bg-zinc-900 border-2 border-zinc-800 rounded-2xl p-4 cursor-pointer
        hover:border-emerald-500/50 transition-all relative overflow-hidden
        ${isStrong ? 'animate-pulse-slow' : ''}
      `}
      style={
        isStrong
          ? {
              boxShadow: '0 0 20px rgba(16, 185, 129, 0.2)',
            }
          : {}
      }
    >
      {/* Main Content */}
      <div className="flex items-center gap-4">
        {/* Ticker Icon */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-xl flex items-center justify-center border border-emerald-500/30">
            <span className="text-lg font-bold text-emerald-400">{ticker.substring(0, 2)}</span>
          </div>
        </div>

        {/* Company Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="font-bold text-white text-lg">{ticker}</p>
            <div className="relative">
              <motion.div
                className={`px-3 py-1 rounded-full border ${signalBg} flex items-center gap-1.5`}
                onHoverStart={() => setShowTooltip(true)}
                onHoverEnd={() => setShowTooltip(false)}
              >
                <SignalIcon className={signalColor} size={14} />
                <span className={`text-xs font-semibold ${signalColor}`}>
                  {data.signal.signal_strength}
                </span>
                <Info size={12} className="text-zinc-500" />
              </motion.div>

              {/* Tooltip */}
              <AnimatePresence>
                {showTooltip && (
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 5 }}
                    className="absolute top-full left-0 mt-2 w-64 bg-zinc-800 border border-zinc-700 rounded-xl p-3 z-10 backdrop-blur-sm"
                  >
                    <p className="text-xs text-zinc-300">
                      {isLong && 'Bonds are overpriced. Equity-implied risk is lower than market prices.'}
                      {isShort && 'Bonds are underpriced. Equity-implied risk is higher than market prices.'}
                      {!isLong && !isShort && 'No significant mispricing detected.'}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
          <p className="text-sm text-zinc-400 truncate">{data.company.company_name}</p>
        </div>

        {/* Sparkline Chart */}
        <div className="hidden md:block w-24 h-12">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData}>
              <Line
                type="monotone"
                dataKey="dd"
                stroke={isLong ? '#10b981' : isShort ? '#ef4444' : '#71717a'}
                strokeWidth={2}
                dot={false}
                animationDuration={1000}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Metrics */}
        <div className="hidden lg:grid grid-cols-2 gap-4 min-w-[280px]">
          <div className="text-right">
            <p className="text-xs text-zinc-500 mb-1">Theo Spread</p>
            <p className="text-sm font-bold text-white">
              <CountUp end={data.merton.theo_spread_bps} decimals={0} duration={1} /> bps
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-zinc-500 mb-1">Market Spread</p>
            <p className="text-sm font-bold text-white">
              <CountUp end={data.market_spread_bps} decimals={0} duration={1} /> bps
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <AnimatePresence>
          {showActions && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex items-center gap-2"
            >
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 hover:bg-blue-500/20 rounded-lg transition-colors"
                title="Set alert"
              >
                <Bell className="text-blue-400" size={18} />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove();
                }}
                className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                title="Remove from watchlist"
              >
                <Trash2 className="text-red-400" size={18} />
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Mobile Actions (always visible on mobile) */}
      <div className="md:hidden flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
        <div className="flex gap-4 text-xs">
          <div>
            <span className="text-zinc-500">Theo: </span>
            <span className="text-white font-medium">{data.merton.theo_spread_bps.toFixed(0)} bps</span>
          </div>
          <div>
            <span className="text-zinc-500">Market: </span>
            <span className="text-white font-medium">{data.market_spread_bps.toFixed(0)} bps</span>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="p-2 hover:bg-blue-500/20 rounded-lg">
            <Bell className="text-blue-400" size={16} />
          </button>
          <button onClick={onRemove} className="p-2 hover:bg-red-500/20 rounded-lg">
            <Trash2 className="text-red-400" size={16} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}