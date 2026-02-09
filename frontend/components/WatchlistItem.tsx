'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
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

  // Mock sparkline data
  const sparklineData = Array.from({ length: 7 }, (_, i) => ({
    day: i,
    dd: data ? data.merton.distance_to_default + (Math.random() - 0.5) * 0.5 : 0,
  }));

  const isLong = data && data.signal.spread_diff_bps < -75;
  const isShort = data && data.signal.spread_diff_bps > 75;
  const SignalIcon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;

  if (loading) {
    return (
      <div className="bg-zinc-950 border-b border-zinc-900 p-6 animate-pulse flex items-center gap-4">
        <div className="h-8 w-8 bg-zinc-900" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-zinc-900 w-24" />
          <div className="h-3 bg-zinc-900 w-32" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, height: 0 }}
      onHoverStart={() => setShowActions(true)}
      onHoverEnd={() => setShowActions(false)}
      className="group bg-black border-b border-zinc-900 p-6 hover:bg-zinc-950 transition-colors cursor-pointer flex items-center justify-between"
    >
      <div className="flex items-center gap-8">
        <div className="w-12 h-12 flex items-center justify-center border border-zinc-800 bg-zinc-950 group-hover:border-zinc-700 transition-colors">
          <span className="font-serif font-bold text-white tracking-widest">{ticker.substring(0, 2)}</span>
        </div>

        <div>
          <div className="flex items-center gap-3">
            <h3 className="font-serif text-lg text-white tracking-wider">{ticker}</h3>
            <div className={`flex items-center gap-1 px-2 py-0.5 border border-zinc-800 ${isLong ? 'text-white' : isShort ? 'text-white' : 'text-zinc-600'}`}>
              <SignalIcon size={10} />
              <span className="text-[9px] font-bold uppercase tracking-wider">{data.signal.signal_strength}</span>
            </div>
          </div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-widest mt-1">{data.company.company_name}</p>
        </div>
      </div>

      <div className="hidden md:flex items-center gap-12">
        {/* Sparkline */}
        <div className="w-24 h-8 opacity-40 grayscale group-hover:grayscale-0 transition-all">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData}>
              <Line type="step" dataKey="dd" stroke="#fff" strokeWidth={1} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Metrics */}
        <div className="text-right w-24">
          <p className="text-[9px] text-zinc-600 uppercase tracking-widest mb-1">Theo Spread</p>
          <p className="text-sm font-serif text-white"><CountUp end={data.merton.theo_spread_bps} decimals={0} /> bps</p>
        </div>
        
        <div className="text-right w-24">
          <p className="text-[9px] text-zinc-600 uppercase tracking-widest mb-1">Market</p>
          <p className="text-sm font-serif text-white"><CountUp end={data.market_spread_bps} decimals={0} /> bps</p>
        </div>
      </div>

      {/* Remove Button */}
      <div className="w-8 flex justify-end">
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="text-zinc-800 hover:text-red-600 transition-colors"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </motion.div>
  );
}