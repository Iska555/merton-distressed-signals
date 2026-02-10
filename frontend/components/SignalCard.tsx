'use client';

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

  const Icon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;
  const iconColor = isLong ? 'text-emerald-500' : isShort ? 'text-red-500' : 'text-zinc-500';

  return (
    <div className="border-2 border-zinc-800 bg-black">
      <div className="p-8 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`p-3 border border-zinc-800 ${iconColor}`}>
            <Icon size={24} />
          </div>
          <div>
            <h3 className="text-2xl font-serif text-white tracking-wide uppercase">
              {signal}
            </h3>
            <p className="text-[10px] text-zinc-600 uppercase tracking-widest font-mono mt-1">
              Model recommendation
            </p>
          </div>
        </div>
        <div className="text-4xl font-serif text-white tracking-wider">
          {signalStrength}
        </div>
      </div>

      <div className="grid grid-cols-3 border-b border-zinc-800">
        <div className="p-8 border-r border-zinc-800 hover:bg-zinc-950 transition-colors">
          <p className="text-zinc-500 text-[9px] uppercase tracking-[0.25em] mb-3 font-mono">
            Theoretical
          </p>
          <p className="text-3xl font-serif text-white">
            <CountUp end={theoSpread} decimals={0} duration={1.5} /> bps
          </p>
        </div>
        <div className="p-8 border-r border-zinc-800 hover:bg-zinc-950 transition-colors">
          <p className="text-zinc-500 text-[9px] uppercase tracking-[0.25em] mb-3 font-mono">
            Market
          </p>
          <p className="text-3xl font-serif text-white">
            <CountUp end={marketSpread} decimals={0} duration={1.5} /> bps
          </p>
        </div>
        <div className="p-8 hover:bg-zinc-950 transition-colors">
          <p className="text-zinc-500 text-[9px] uppercase tracking-[0.25em] mb-3 font-mono">
            Difference
          </p>
          <p className={`text-3xl font-serif ${iconColor}`}>
            <CountUp
              end={spreadDiff}
              decimals={0}
              duration={1.5}
              prefix={spreadDiff > 0 ? '+' : ''}
            /> bps
          </p>
        </div>
      </div>

      <div className="p-6 text-[11px] text-zinc-500 font-mono leading-relaxed">
        {isLong && '→ Bonds overpriced relative to equity-implied risk. Consider long credit position.'}
        {isShort && '→ Bonds underpriced relative to equity-implied risk. Consider short credit position.'}
        {isNeutral && '→ No significant mispricing detected. Hold or avoid position.'}
      </div>
    </div>
  );
}