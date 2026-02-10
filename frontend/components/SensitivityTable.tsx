'use client';

import { SensitivityResponse } from '@/lib/api';
import { CheckCircle2, XCircle, Activity } from 'lucide-react';

interface SensitivityTableProps {
  sensitivity: SensitivityResponse;
}

export default function SensitivityTable({ sensitivity }: SensitivityTableProps) {
  return (
    <div className="border border-zinc-800 bg-black">
      <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-900 text-white border border-zinc-800">
            <Activity size={16} />
          </div>
          <h3 className="font-serif text-lg tracking-wide text-white uppercase">
            Sensitivity Matrix
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {sensitivity.is_robust ? (
            <>
              <CheckCircle2 className="text-emerald-500" size={16} />
              <span className="text-emerald-500 font-mono text-[10px] uppercase tracking-widest">
                Robust Signal
              </span>
            </>
          ) : (
            <>
              <XCircle className="text-red-500" size={16} />
              <span className="text-red-500 font-mono text-[10px] uppercase tracking-widest">
                Fragile Signal
              </span>
            </>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="border-b border-zinc-800">
            <tr className="bg-zinc-950">
              <th className="text-left py-4 px-6 text-zinc-500 text-[9px] font-mono uppercase tracking-[0.25em]">
                Vol Shock
              </th>
              <th className="text-right py-4 px-6 text-zinc-500 text-[9px] font-mono uppercase tracking-[0.25em]">
                Sigma_E
              </th>
              <th className="text-right py-4 px-6 text-zinc-500 text-[9px] font-mono uppercase tracking-[0.25em]">
                Theo Spread
              </th>
              <th className="text-right py-4 px-6 text-zinc-500 text-[9px] font-mono uppercase tracking-[0.25em]">
                Δ Spread
              </th>
            </tr>
          </thead>
          <tbody>
            {sensitivity.volatility_sensitivity.map((row, idx) => {
              const isBase = row.shock_pct === 0;
              return (
                <tr
                  key={idx}
                  className={`border-b border-zinc-900 hover:bg-zinc-950 transition-colors ${
                    isBase ? 'bg-zinc-950' : ''
                  }`}
                >
                  <td className="py-4 px-6 text-white font-mono text-sm">
                    {row.shock_pct > 0 ? '+' : ''}
                    {row.shock_pct.toFixed(0)}%
                  </td>
                  <td className="py-4 px-6 text-right text-zinc-300 font-mono text-sm">
                    {(row.sigma_E * 100).toFixed(1)}%
                  </td>
                  <td className="py-4 px-6 text-right text-white font-serif text-sm">
                    {row.theo_spread_bps.toFixed(0)} bps
                  </td>
                  <td
                    className={`py-4 px-6 text-right font-mono text-sm ${
                      row.spread_change_bps > 0
                        ? 'text-red-500'
                        : row.spread_change_bps < 0
                        ? 'text-emerald-500'
                        : 'text-zinc-500'
                    }`}
                  >
                    {row.spread_change_bps > 0 ? '+' : ''}
                    {row.spread_change_bps.toFixed(0)} bps
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-2 border-t border-zinc-800">
        <div className="p-6 border-r border-zinc-800 hover:bg-zinc-950 transition-colors">
          <p className="text-zinc-500 text-[9px] uppercase tracking-[0.25em] mb-2 font-mono">
            Spread Range (±20%)
          </p>
          <p className="text-2xl font-serif text-white">
            {sensitivity.spread_range.toFixed(0)} bps
          </p>
        </div>
        <div className="p-6 hover:bg-zinc-950 transition-colors">
          <p className="text-zinc-500 text-[9px] uppercase tracking-[0.25em] mb-2 font-mono">
            Spread Std Dev
          </p>
          <p className="text-2xl font-serif text-white">
            {sensitivity.spread_std.toFixed(0)} bps
          </p>
        </div>
      </div>
    </div>
  );
}