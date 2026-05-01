'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { MertonEventResult } from '@/lib/api';

interface Props {
  result: MertonEventResult;
}

const SIGNAL_CONFIG = {
  CRITICAL_SHORT: {
    border: 'border-l-red-600',
    badge:  'bg-red-950/60 text-red-400 border border-red-800',
    bar:    'bg-red-600',
    text:   'text-red-400',
  },
  SHORT_CREDIT: {
    border: 'border-l-orange-500',
    badge:  'bg-orange-950/60 text-orange-400 border border-orange-700',
    bar:    'bg-orange-500',
    text:   'text-orange-400',
  },
  NEUTRAL: {
    border: 'border-l-zinc-700',
    badge:  'bg-zinc-900 text-zinc-500 border border-zinc-700',
    bar:    'bg-zinc-600',
    text:   'text-zinc-400',
  },
  LONG_CREDIT: {
    border: 'border-l-emerald-600',
    badge:  'bg-emerald-950/60 text-emerald-400 border border-emerald-700',
    bar:    'bg-emerald-600',
    text:   'text-emerald-400',
  },
} as const;

const fmt     = (n: number, d = 1)  => n.toFixed(d);
const fmtPct  = (n: number)         => `${n >= 0 ? '+' : ''}${(n * 100).toFixed(2)}%`;
const fmtBps  = (n: number)         => `${n >= 0 ? '+' : ''}${fmt(n)} bps`;

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: string }) {
  return (
    <div>
      <p className="text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-mono mb-1">{label}</p>
      <p className={`text-[12px] font-mono ${highlight ?? 'text-zinc-300'}`}>{value}</p>
    </div>
  );
}

export default function EventCard({ result }: Props) {
  const [expanded, setExpanded] = useState(false);

  const cfg      = SIGNAL_CONFIG[result.signal] ?? SIGNAL_CONFIG.NEUTRAL;
  const gapWidth = Math.min((Math.abs(result.alpha_gap_bps) / 2000) * 100, 100);
  const isCrit   = result.signal === 'CRITICAL_SHORT';

  return (
    <div className={`border-l-2 ${cfg.border} border-b border-zinc-900 transition-colors hover:bg-zinc-950/40`}>

      {/* Collapsed row */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-4 px-4 py-3 text-left min-w-max group"
        aria-expanded={expanded}
      >
        {/* Ticker */}
        <span className="w-24 text-sm font-mono text-white font-semibold tracking-wider flex items-center gap-1.5">
          {isCrit && <AlertTriangle size={11} className="text-red-500 shrink-0" />}
          {result.ticker}
        </span>

        {/* Signal badge */}
        <span className={`w-36 text-[10px] font-mono px-2 py-0.5 uppercase tracking-wider inline-block ${cfg.badge}`}>
          {result.signal.replace('_', ' ')}
        </span>

        {/* Theo spread */}
        <span className="w-28 text-[11px] font-mono text-zinc-300">
          {fmt(result.theoretical_spread_bps)} bps
        </span>

        {/* Market spread */}
        <span className="w-28 text-[11px] font-mono text-zinc-500">
          {fmt(result.market_spread_bps)} bps
        </span>

        {/* Alpha gap */}
        <span className={`w-28 text-[11px] font-mono font-bold ${cfg.text}`}>
          {fmtBps(result.alpha_gap_bps)}
        </span>

        {/* Distance to default */}
        <span className="w-20 text-[11px] font-mono text-zinc-400">
          {fmt(result.distance_to_default, 2)}σ
        </span>

        {/* Default probability */}
        <span className="w-20 text-[11px] font-mono text-zinc-400">
          {fmt(result.default_probability_pct, 2)}%
        </span>

        {/* Trigger type */}
        <span className="w-28 text-[10px] font-mono text-zinc-600 uppercase">
          {result.trigger_type.replace('_', ' ')}
        </span>

        {/* Price change */}
        <span className={`w-24 text-[11px] font-mono ${result.price_change_pct < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
          {fmtPct(result.price_change_pct)}
        </span>

        {/* Company name */}
        <span className="flex-1 text-[11px] font-mono text-zinc-600 text-right truncate max-w-[200px] pr-2">
          {result.company_name}
        </span>

        {/* Chevron */}
        <span className="text-zinc-700 group-hover:text-zinc-400 transition-colors shrink-0">
          {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </span>
      </button>

      {/* Detail drawer */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            key="drawer"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-6 pt-2 pb-5 bg-zinc-950 border-t border-zinc-900 space-y-4">

              {/* Alpha gap progress bar */}
              <div>
                <div className="flex justify-between text-[9px] font-mono text-zinc-600 uppercase tracking-widest mb-1.5">
                  <span>Alpha Gap Magnitude</span>
                  <span>{fmt(result.alpha_gap_bps)} bps / 2000 bps ceiling</span>
                </div>
                <div className="h-[3px] w-full bg-zinc-900 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${cfg.bar} transition-all duration-500`}
                    style={{ width: `${gapWidth}%` }}
                  />
                </div>
              </div>

              {/* Structural metrics grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Metric label="Equity Value"       value={`$${result.equity_value_b.toFixed(2)}B`} />
                <Metric label="Face Value Debt"    value={`$${result.face_value_debt_b.toFixed(2)}B`} />
                <Metric label="Equity Vol"         value={`${(result.equity_vol * 100).toFixed(1)}%`} />
                <Metric label="Implied Asset Vol"  value={`${(result.implied_asset_vol * 100).toFixed(1)}%`} />
                <Metric label="Implied Asset V"    value={`$${result.implied_asset_value_b.toFixed(2)}B`} />
                <Metric label="Risk-Free Rate"     value={`${(result.risk_free_rate * 100).toFixed(2)}%`} />
                <Metric label="ΔVol"               value={fmtPct(result.vol_change_pct)} />
                <Metric
                  label="Solver"
                  value={result.solver_converged ? 'CONVERGED' : 'FALLBACK'}
                  highlight={result.solver_converged ? 'text-zinc-300' : 'text-amber-400'}
                />
              </div>

              {/* Error notice */}
              {result.error && (
                <p className="text-[10px] font-mono text-red-500 border border-red-900 bg-red-950/30 px-3 py-2">
                  ⚠ {result.error}
                </p>
              )}

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}