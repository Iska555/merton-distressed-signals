'use client';

import { motion } from 'framer-motion';
import { SensitivityResponse } from '@/lib/api';
import { CheckCircle2, XCircle } from 'lucide-react';

interface SensitivityTableProps {
  sensitivity: SensitivityResponse;
}

export default function SensitivityTable({ sensitivity }: SensitivityTableProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="bg-zinc-900 rounded-3xl p-8 border border-zinc-800"
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span className="text-purple-400">🔬</span>
          Sensitivity Analysis
        </h2>
        <div className="flex items-center gap-2">
          {sensitivity.is_robust ? (
            <>
              <CheckCircle2 className="text-emerald-400" size={24} />
              <span className="text-emerald-400 font-semibold">Signal is ROBUST</span>
            </>
          ) : (
            <>
              <XCircle className="text-red-400" size={24} />
              <span className="text-red-400 font-semibold">Signal is FRAGILE</span>
            </>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left py-3 px-4 text-zinc-400 text-sm font-medium">Vol Shock</th>
              <th className="text-right py-3 px-4 text-zinc-400 text-sm font-medium">Sigma_E</th>
              <th className="text-right py-3 px-4 text-zinc-400 text-sm font-medium">Theo Spread</th>
              <th className="text-right py-3 px-4 text-zinc-400 text-sm font-medium">Change</th>
            </tr>
          </thead>
          <tbody>
            {sensitivity.volatility_sensitivity.map((row, idx) => {
              const isBase = row.shock_pct === 0;
              return (
                <motion.tr
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.05 }}
                  className={`border-b border-zinc-800/50 ${
                    isBase ? 'bg-emerald-500/10' : 'hover:bg-zinc-800/30'
                  }`}
                >
                  <td className="py-3 px-4 text-white font-medium">
                    {row.shock_pct > 0 ? '+' : ''}
                    {row.shock_pct.toFixed(0)}%
                  </td>
                  <td className="py-3 px-4 text-right text-zinc-300">
                    {(row.sigma_E * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 text-right text-white font-medium">
                    {row.theo_spread_bps.toFixed(0)} bps
                  </td>
                  <td
                    className={`py-3 px-4 text-right font-medium ${
                      row.spread_change_bps > 0
                        ? 'text-red-400'
                        : row.spread_change_bps < 0
                        ? 'text-emerald-400'
                        : 'text-zinc-400'
                    }`}
                  >
                    {row.spread_change_bps > 0 ? '+' : ''}
                    {row.spread_change_bps.toFixed(0)} bps
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 pt-6 border-t border-zinc-800 grid grid-cols-2 gap-4">
        <div>
          <p className="text-zinc-400 text-sm mb-1">Spread Range (±20% vol)</p>
          <p className="text-xl font-bold text-white">{sensitivity.spread_range.toFixed(0)} bps</p>
        </div>
        <div>
          <p className="text-zinc-400 text-sm mb-1">Spread Std Dev</p>
          <p className="text-xl font-bold text-white">{sensitivity.spread_std.toFixed(0)} bps</p>
        </div>
      </div>
    </motion.div>
  );
}