'use client';

import { motion } from 'framer-motion';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface SpreadChartProps {
  theoSpread: number;
  marketSpread: number;
  volatilitySensitivity?: Array<{
    shock_pct: number;
    theo_spread_bps: number;
  }>;
}

export default function SpreadChart({
  theoSpread,
  marketSpread,
  volatilitySensitivity,
}: SpreadChartProps) {
  // Generate data for the chart
  const data = volatilitySensitivity || [
    { vol_shock: -20, spread: theoSpread * 0.85 },
    { vol_shock: -10, spread: theoSpread * 0.92 },
    { vol_shock: 0, spread: theoSpread },
    { vol_shock: 10, spread: theoSpread * 1.08 },
    { vol_shock: 20, spread: theoSpread * 1.18 },
  ];

  const chartData = data.map((d) => ({
    name: `${d.vol_shock || d.shock_pct}%`,
    theoretical: volatilitySensitivity ? d.theo_spread_bps : d.spread,
    market: marketSpread,
  }));

  const isLongSignal = theoSpread < marketSpread;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="bg-zinc-900 rounded-3xl p-8 border border-zinc-800"
    >
      <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <span className="text-blue-400">📊</span>
        Spread Sensitivity to Volatility
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorTheo" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor={isLongSignal ? '#10b981' : '#ef4444'}
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor={isLongSignal ? '#10b981' : '#ef4444'}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="name"
            stroke="#71717a"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#71717a"
            style={{ fontSize: '12px' }}
            label={{ value: 'Spread (bps)', angle: -90, position: 'insideLeft', fill: '#71717a' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#18181b',
              border: '1px solid #3f3f46',
              borderRadius: '12px',
              color: '#fff',
            }}
            formatter={(value: number) => [`${value.toFixed(0)} bps`, '']}
          />
          <ReferenceLine
            y={marketSpread}
            stroke="#ef4444"
            strokeDasharray="5 5"
            label={{ value: 'Market Spread', fill: '#ef4444', fontSize: 12 }}
          />
          <Area
            type="monotone"
            dataKey="theoretical"
            stroke={isLongSignal ? '#10b981' : '#ef4444'}
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorTheo)"
            animationDuration={1500}
            animationBegin={300}
            animationEasing="ease-in-out"
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="mt-4 text-sm text-zinc-400 text-center">
        Theoretical spread changes with ±20% equity volatility shocks
      </div>
    </motion.div>
  );
}