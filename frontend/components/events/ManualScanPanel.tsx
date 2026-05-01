'use client';

import { useState, useMemo } from 'react';
import { Terminal, Zap, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

interface Props {
  onScan: (tickers: string[]) => void;
  isScanning: boolean;
}

const PRESETS: { label: string; tickers: string[] }[] = [
  { label: 'Banks',       tickers: ['JPM', 'BAC', 'C', 'WFC', 'GS', 'MS'] },
  { label: 'High Yield',  tickers: ['AMC', 'DISH', 'LUMN', 'CHK', 'NYCB'] },
  { label: 'Industrials', tickers: ['BA', 'GE', 'F', 'GM', 'X', 'NUE'] },
  { label: 'Energy',      tickers: ['CHK', 'CPE', 'SM', 'RRC', 'OXY'] },
];

export function ManualScanPanel({ onScan, isScanning }: Props) {
  const [input, setInput] = useState('');

  const tickers = useMemo(() => {
    return input
      .toUpperCase()
      .split(/[\s,;]+/)
      .map(t => t.trim())
      .filter(t => t.length > 0 && t.length <= 10)
      .slice(0, 20);
  }, [input]);

  const canSubmit = tickers.length > 0 && !isScanning;

  const handleSubmit = () => {
    if (!canSubmit) return;
    onScan(tickers);
  };

  const handlePreset = (presetTickers: string[]) => {
    if (isScanning) return;
    setInput(presetTickers.join(', '));
    onScan(presetTickers);
  };

  return (
    <div className="bg-black flex flex-col">
      {/* ── Header ── */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-zinc-800 bg-zinc-950/50">
        <Terminal size={14} className="text-zinc-500" />
        <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-300">
          Manual Scan Override
        </span>
      </div>

      <div className="p-5 space-y-5">
        {/* ── Ticker Input ── */}
        <div>
          <p className="text-[9px] font-mono text-zinc-600 uppercase tracking-widest mb-2">
            Target Entities (Max 20)
          </p>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
            placeholder="AAPL, TSLA, NYCB..."
            rows={3}
            disabled={isScanning}
            className="w-full bg-zinc-950 border border-zinc-800 text-white font-mono text-xs
              p-3 resize-none placeholder-zinc-800 focus:outline-none focus:border-zinc-500
              uppercase tracking-wider transition-colors disabled:opacity-50"
          />
          <div className="h-4 mt-1">
            {tickers.length > 0 && (
              <p className="text-[9px] font-mono text-emerald-500 uppercase tracking-widest">
                {tickers.length} Entity{tickers.length !== 1 ? 's' : ''} Locked
              </p>
            )}
          </div>
        </div>

        {/* ── Execution Button ── */}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="w-full flex items-center justify-center gap-2 py-3
            text-[10px] font-mono uppercase tracking-widest border transition-all duration-300
            enabled:border-zinc-500 enabled:text-white enabled:hover:bg-zinc-800 enabled:cursor-pointer
            disabled:border-zinc-900 disabled:text-zinc-700 disabled:cursor-not-allowed bg-black"
        >
          <Zap size={12} className={isScanning ? "animate-pulse text-orange-500" : ""} />
          {isScanning ? 'Executing Scan...' : 'Deploy Merton Engine'}
        </button>

        {/* ── Quick Presets ── */}
        <div className="pt-2 border-t border-zinc-900">
          <p className="text-[9px] font-mono text-zinc-600 uppercase tracking-widest mb-3">
            Sector Portfolios
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {PRESETS.map(preset => (
              <button
                key={preset.label}
                onClick={() => handlePreset(preset.tickers)}
                disabled={isScanning}
                className="flex items-center justify-between px-3 py-2.5
                  text-[9px] font-mono uppercase tracking-widest text-zinc-400
                  bg-zinc-950 border border-zinc-900 hover:border-zinc-600 hover:text-zinc-200
                  transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <span>{preset.label}</span>
                <ChevronRight size={10} className="text-zinc-600" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}