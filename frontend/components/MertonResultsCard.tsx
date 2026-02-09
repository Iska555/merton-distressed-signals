'use client';

import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import { MertonOutputs } from '@/lib/api';

interface MertonResultsCardProps {
  merton: MertonOutputs;
  E: number;
  D: number;
}

export default function MertonResultsCard({ merton, E, D }: MertonResultsCardProps) {
  const formatCurrency = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(0)}`;
  };

  const metrics = [
    { label: 'Asset Value (V)', value: merton.V, format: formatCurrency },
    { label: 'Asset Volatility (σ_V)', value: merton.sigma_V * 100, suffix: '%' },
    { label: 'Leverage (D/V)', value: merton.leverage * 100, suffix: '%' },
    { label: 'Distance to Default', value: merton.distance_to_default, suffix: 'σ' },
    { label: 'Default Probability', value: merton.default_probability * 100, suffix: '%' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="bg-zinc-900 rounded-3xl p-8 border border-zinc-800"
    >
      <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <span className="text-emerald-400">⚡</span>
        Merton Model Results
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {metrics.map((metric, idx) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.1 + idx * 0.05 }}
            whileHover={{ scale: 1.02 }}
            className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700/50"
          >
            <p className="text-zinc-400 text-sm mb-2">{metric.label}</p>
            <p className="text-3xl font-bold text-white">
              {metric.format ? (
                metric.format(metric.value)
              ) : (
                <>
                  <CountUp end={metric.value} decimals={2} duration={1.5} />
                  {metric.suffix && <span className="text-emerald-400 ml-1">{metric.suffix}</span>}
                </>
              )}
            </p>
          </motion.div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-zinc-800">
        <p className="text-xs text-zinc-500">
          Solver: <span className="text-emerald-400">{merton.solver_method}</span>
        </p>
      </div>
    </motion.div>
  );
}