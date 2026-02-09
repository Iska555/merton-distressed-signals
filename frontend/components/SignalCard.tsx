'use client';

import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import CountUp from 'react-countup';

interface SignalCardProps {
  signal: string;
  signalStrength: string;
  spreadDiff: number;
  theoSpread: number;
  marketSpread: number;
}

export default function SignalCard({
  signal,
  signalStrength,
  spreadDiff,
  theoSpread,
  marketSpread,
}: SignalCardProps) {
  const isLong = signal.includes('LONG');
  const isShort = signal.includes('SHORT');
  const isNeutral = signal.includes('NEUTRAL');

  const bgColor = isLong
    ? 'from-emerald-500/20 to-teal-500/20 border-emerald-500/50'
    : isShort
    ? 'from-red-500/20 to-orange-500/20 border-red-500/50'
    : 'from-zinc-700/20 to-zinc-600/20 border-zinc-600/50';

  const textColor = isLong ? 'text-emerald-400' : isShort ? 'text-red-400' : 'text-zinc-400';

  const Icon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      whileHover={{ scale: 1.02 }}
      className={`bg-gradient-to-br ${bgColor} rounded-3xl p-8 border-2 backdrop-blur-sm`}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Icon className={textColor} size={32} />
          <h3 className={`text-3xl font-bold ${textColor}`}>{signal}</h3>
        </div>
        <div className="text-4xl">{signalStrength}</div>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <div>
          <p className="text-zinc-400 text-sm mb-1">Theoretical</p>
          <p className="text-2xl font-bold text-white">
            <CountUp end={theoSpread} decimals={0} duration={1.5} /> bps
          </p>
        </div>
        <div>
          <p className="text-zinc-400 text-sm mb-1">Market</p>
          <p className="text-2xl font-bold text-white">
            <CountUp end={marketSpread} decimals={0} duration={1.5} /> bps
          </p>
        </div>
        <div>
          <p className="text-zinc-400 text-sm mb-1">Difference</p>
          <p className={`text-2xl font-bold ${textColor}`}>
            <CountUp end={spreadDiff} decimals={0} duration={1.5} prefix={spreadDiff > 0 ? '+' : ''} /> bps
          </p>
        </div>
      </div>

      <div className="text-sm text-zinc-400">
        {isLong && '🟢 Bonds are overpriced relative to equity-implied risk. Consider long credit position.'}
        {isShort && '🔴 Bonds are underpriced relative to equity-implied risk. Consider short credit position.'}
        {isNeutral && '⚪ No significant mispricing detected. Hold or avoid position.'}
      </div>
    </motion.div>
  );
}