'use client';

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
import { TrendingUp } from 'lucide-react';

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
  // Normalize data structure - this fixes the TypeScript error
  const rawData = volatilitySensitivity 
    ? volatilitySensitivity.map(d => ({
        shock: d.shock_pct,
        spread: d.theo_spread_bps
      }))
    : [
        { shock: -20, spread: theoSpread * 0.85 },
        { shock: -10, spread: theoSpread * 0.92 },
        { shock: 0, spread: theoSpread },
        { shock: 10, spread: theoSpread * 1.08 },
        { shock: 20, spread: theoSpread * 1.18 },
      ];

  const chartData = rawData.map((d) => ({
    name: `${d.shock > 0 ? '+' : ''}${d.shock}%`,
    theoretical: d.spread,
    market: marketSpread,
  }));

  const isLongSignal = theoSpread < marketSpread;
  const strokeColor = isLongSignal ? '#10b981' : '#ef4444';
  const glowColor = isLongSignal ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)';

  return (
    <div className="border border-zinc-800 bg-black">
      <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-900 text-white border border-zinc-800">
            <TrendingUp size={16} />
          </div>
          <h3 className="font-serif text-lg tracking-wide text-white uppercase">
            Volatility Sensitivity
          </h3>
        </div>
        <div className="text-[10px] text-zinc-600 uppercase tracking-widest font-mono">
          Spread vs. Vol Shock
        </div>
      </div>

      <div className="p-8">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorTheo" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={strokeColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              dataKey="name"
              stroke="#71717a"
              style={{ fontSize: '10px', fontFamily: 'monospace' }}
            />
            <YAxis
              stroke="#71717a"
              style={{ fontSize: '10px', fontFamily: 'monospace' }}
              label={{ 
                value: 'Spread (bps)', 
                angle: -90, 
                position: 'insideLeft', 
                fill: '#71717a',
                style: { fontSize: '10px', fontFamily: 'monospace' }
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#000',
                border: '1px solid #27272a',
                borderRadius: '0',
                color: '#fff',
                fontSize: '11px',
                fontFamily: 'monospace',
              }}
              formatter={(value: any) => [`${Number(value).toFixed(0)} bps`, '']}
            />
            <ReferenceLine
              y={marketSpread}
              stroke="#71717a"
              strokeDasharray="3 3"
              label={{ 
                value: 'Market', 
                fill: '#71717a', 
                fontSize: 10,
                position: 'right',
                fontFamily: 'monospace'
              }}
            />
            <Area
              type="monotone"
              dataKey="theoretical"
              stroke={strokeColor}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorTheo)"
              animationDuration={1500}
              animationBegin={300}
              animationEasing="ease-in-out"
              style={{
                filter: `drop-shadow(0px 0px 8px ${glowColor})`,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>

        <div className="mt-6 text-[10px] text-zinc-600 text-center uppercase tracking-widest font-mono border-t border-zinc-900 pt-4">
          Theoretical spread response to ±20% equity volatility shock
        </div>
      </div>
    </div>
  );
}