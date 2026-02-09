'use client';

import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import { Layers } from 'lucide-react';

interface MertonResultsProps {
  merton: {
    // Make these optional to match the API response exactly
    V?: number;
    sigma_V?: number;
    distance_to_default: number;
    default_prob?: number;
    theo_spread_bps: number;
    // Keep these as extra fallbacks
    asset_value?: number;
    asset_volatility?: number;
    default_prob_1yr?: number;
  };
  E: number;
  D: number;
}

export default function MertonResultsCard({ merton, E, D }: MertonResultsProps) {
  // Safe extraction with fallbacks to 0
  const assetValue = merton.V ?? merton.asset_value ?? 0;
  const assetVol = merton.sigma_V ?? merton.asset_volatility ?? 0;
  const defaultProb = merton.default_prob ?? merton.default_prob_1yr ?? 0;

  return (
    <div className="border border-zinc-800 bg-black">
      <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-900 text-white border border-zinc-800">
            <Layers size={16} />
          </div>
          <h3 className="font-serif text-lg tracking-wide text-white uppercase">Structural Model Output</h3>
        </div>
        <div className="text-[10px] text-zinc-600 uppercase tracking-widest font-mono">
          Black-Scholes-Merton (1974)
        </div>
      </div>

      <div className="grid md:grid-cols-2">
        {/* Asset Value (V) */}
        <div className="p-8 border-b md:border-b-0 md:border-r border-zinc-800 hover:bg-zinc-950 transition-colors group">
          <p className="text-[9px] text-zinc-500 uppercase tracking-[0.25em] mb-3 font-bold group-hover:text-zinc-400 transition-colors">
            Implied Asset Value (V)
          </p>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-serif text-white tracking-tight">
              <CountUp end={assetValue / 1e12} decimals={2} prefix="$" suffix="T" duration={1.5} />
            </span>
          </div>
          <p className="text-[10px] text-zinc-600 mt-2 font-mono uppercase tracking-wider">Market Cap + Debt (Adj)</p>
        </div>

        {/* Asset Volatility (sigma_V) */}
        <div className="p-8 border-b md:border-b-0 border-zinc-800 hover:bg-zinc-950 transition-colors group">
          <p className="text-[9px] text-zinc-500 uppercase tracking-[0.25em] mb-3 font-bold group-hover:text-zinc-400 transition-colors">
            Asset Volatility (σ_V)
          </p>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-serif text-white tracking-tight">
              <CountUp end={assetVol * 100} decimals={2} suffix="%" duration={1.5} />
            </span>
          </div>
          <p className="text-[10px] text-zinc-600 mt-2 font-mono uppercase tracking-wider">De-levered Equity Vol</p>
        </div>

        {/* Distance to Default */}
        <div className="p-8 border-b md:border-b-0 md:border-r border-zinc-800 hover:bg-zinc-950 transition-colors group">
          <p className="text-[9px] text-zinc-500 uppercase tracking-[0.25em] mb-3 font-bold group-hover:text-zinc-400 transition-colors">
            Distance to Default (DD)
          </p>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-serif text-white tracking-tight">
              <CountUp end={merton.distance_to_default} decimals={2} suffix="σ" duration={1.5} />
            </span>
          </div>
          <p className="text-[10px] text-zinc-600 mt-2 font-mono uppercase tracking-wider">Std Devs from Insolvency</p>
        </div>

        {/* Default Probability */}
        <div className="p-8 hover:bg-zinc-950 transition-colors group">
          <p className="text-[9px] text-zinc-500 uppercase tracking-[0.25em] mb-3 font-bold group-hover:text-zinc-400 transition-colors">
            1-Year Default Prob
          </p>
          <div className="flex items-baseline gap-2">
            <span className={`text-4xl font-serif tracking-tight ${defaultProb > 0.05 ? 'text-red-500' : 'text-white'}`}>
              {(defaultProb * 100).toFixed(4)}%
            </span>
          </div>
          <p className="text-[10px] text-zinc-600 mt-2 font-mono uppercase tracking-wider">Normal Dist N(-DD)</p>
        </div>
      </div>
    </div>
  );
}