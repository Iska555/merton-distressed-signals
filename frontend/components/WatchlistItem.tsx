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
  
  // Monochrome Signal Icons
  const SignalIcon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;
  // Use White/Gray for signals instead of Green/Red
  const signalColor = 'text-white'; 
  const signalBg = 'bg-zinc-800 border-zinc-700';

  // Skeleton loader
  if (loading) {
    return (
      <div className="bg-zinc-950 border border-zinc-900 p-4 animate-pulse border-l-2 border-l-zinc-800">
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 bg-zinc-900"></div>
          <div className="flex-1">
            <div className="h-4 bg-zinc-900 w-1/3 mb-2"></div>
            <div className="h-3 bg-zinc-900 w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (!data) {
    return (
      <div className="bg-zinc-950 border border-zinc-900 p-4 border-l-2 border-l-red-900">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-serif font-bold text-white tracking-widest">{ticker}</p>
            <p className="text-xs text-red-900 uppercase tracking-wider">Data Unavailable</p>
          </div>
          <button onClick={onRemove} className="p-2 hover:bg-zinc-900 transition-colors">
            <Trash2 className="text-zinc-600 hover:text-red-900" size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ delay: index * 0.05 }}
      layout
      onHoverStart={() => setShowActions(true)}
      onHoverEnd={() => setShowActions(false)}
      className="group bg-zinc-950 border border-zinc-900 p-5 cursor-pointer hover:bg-zinc-900 transition-all relative border-l-2 border-l-zinc-500 hover:border-l-white"
    >
      {/* Main Content */}
      <div className="flex items-center gap-6">
        {/* Ticker Box - Sharp Edges */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-zinc-900 flex items-center justify-center border border-zinc-800">
            <span className="text-sm font-serif font-bold text-white tracking-widest">{ticker.substring(0, 2)}</span>
          </div>
        </div>

        {/* Company Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <p className="font-serif font-bold text-white text-lg tracking-wider">{ticker}</p>
            
            {/* Signal Badge - Monochrome */}
            <div className="relative">
              <div 
                className={`px-2 py-0.5 border ${signalBg} flex items-center gap-1.5`}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
              >
                <SignalIcon className="text-zinc-400" size={12} />
                <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-300">
                  {data.signal.signal_strength}
                </span>
              </div>

               {/* Tooltip */}
               <AnimatePresence>
                {showTooltip && (
                  <motion.div
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 5 }}
                    className="absolute top-full left-0 mt-2 w-64 bg-zinc-900 border border-zinc-800 p-3 z-10 shadow-2xl"
                  >
                    <p className="text-[10px] text-zinc-400 uppercase tracking-wide leading-relaxed">
                      {isLong && 'Equity markets imply lower risk than bonds.'}
                      {isShort && 'Equity markets imply higher risk than bonds.'}
                      {!isLong && !isShort && 'Fairly valued.'}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-widest truncate">{data.company.company_name}</p>
        </div>

        {/* Sparkline Chart - Monochrome */}
        <div className="hidden md:block w-32 h-10 opacity-50 group-hover:opacity-100 transition-opacity">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData}>
              <Line
                type="step" // Step line fits the technical look better
                dataKey="dd"
                stroke="#d4d4d8" // Zinc-300
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Metrics - Institutional Layout */}
        <div className="hidden lg:grid grid-cols-2 gap-8 min-w-[240px] border-l border-zinc-900 pl-6">
          <div>
            <p className="text-[9px] text-zinc-600 uppercase tracking-widest mb-1">Theo Spread</p>
            <p className="text-sm font-serif text-white">
              <CountUp end={data.merton.theo_spread_bps} decimals={0} duration={1} /> <span className="text-[9px] text-zinc-600">BPS</span>
            </p>
          </div>
          <div>
            <p className="text-[9px] text-zinc-600 uppercase tracking-widest mb-1">Market</p>
            <p className="text-sm font-serif text-white">
              <CountUp end={data.market_spread_bps} decimals={0} duration={1} /> <span className="text-[9px] text-zinc-600">BPS</span>
            </p>
          </div>
        </div>

        {/* Action Buttons - Reveal on Hover */}
        <div className="w-8 flex justify-end">
           <button 
             onClick={(e) => {
               e.stopPropagation();
               onRemove();
             }}
             className="text-zinc-700 hover:text-white transition-colors"
           >
             <Trash2 size={14} />
           </button>
        </div>
      </div>
      
      {/* Mobile Stats Row */}
      <div className="md:hidden mt-4 pt-3 border-t border-zinc-900 flex justify-between text-[10px] uppercase tracking-wider text-zinc-500">
         <span>Theo: <span className="text-white">{data.merton.theo_spread_bps.toFixed(0)}</span></span>
         <span>Mkt: <span className="text-white">{data.market_spread_bps.toFixed(0)}</span></span>
      </div>
    </motion.div>
  );
}