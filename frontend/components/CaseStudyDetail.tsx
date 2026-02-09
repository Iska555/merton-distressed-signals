'use client';

import { motion } from 'framer-motion';
import { ArrowLeft, TrendingDown } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from 'recharts';

interface CaseStudyDetailProps {
  caseStudy: any;
  onBack: () => void;
}

export default function CaseStudyDetail({ caseStudy, onBack }: CaseStudyDetailProps) {
  // Prepare chart data
  const chartData = caseStudy.timeline
    .filter((t: any) => t.dd !== null)
    .map((t: any) => ({
      date: t.label,
      dd: t.dd,
      threshold: 0,
      warning: 2,
    }));

  return (
    <div className="min-h-screen bg-black text-white pb-20 md:pb-0">
      {/* Header */}
      <header className="border-b border-zinc-800 backdrop-blur-sm bg-black/50 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
            Back to Case Studies
          </button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 max-w-6xl">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="text-8xl mb-6">{caseStudy.icon}</div>
          <h1 className="text-5xl font-bold mb-4">{caseStudy.title}</h1>
          <p className="text-2xl text-zinc-400 mb-6">{caseStudy.subtitle}</p>
          <div className="inline-block bg-red-500/20 border border-red-500/50 rounded-full px-6 py-2">
            <span className="text-red-400 font-semibold">OUTCOME: {caseStudy.outcome}</span>
          </div>
        </motion.div>

        {/* Metrics Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12"
        >
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <p className="text-zinc-400 text-sm mb-2">Early Warning</p>
            <p className="text-3xl font-bold text-emerald-400">{caseStudy.metrics.leadTime}</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <p className="text-zinc-400 text-sm mb-2">Max DD</p>
            <p className="text-3xl font-bold text-white">{caseStudy.metrics.maxDD}σ</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <p className="text-zinc-400 text-sm mb-2">Min DD</p>
            <p className="text-3xl font-bold text-red-400">{caseStudy.metrics.minDD}σ</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
            <p className="text-zinc-400 text-sm mb-2">Peak Spread Diff</p>
            <p className="text-3xl font-bold text-orange-400">
              {caseStudy.metrics.peakSpreadDiff} bps
            </p>
          </div>
        </motion.div>

        {/* Distance to Default Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 mb-12"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <TrendingDown className="text-red-400" />
            Distance to Default Over Time
          </h2>

          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="ddGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" stroke="#71717a" />
              <YAxis stroke="#71717a" label={{ value: 'Distance to Default (σ)', angle: -90, position: 'insideLeft', fill: '#71717a' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  border: '1px solid #3f3f46',
                  borderRadius: '12px',
                }}
              />
              <ReferenceLine
                y={0}
                stroke="#ef4444"
                strokeWidth={2}
                label={{ value: 'Default Threshold', fill: '#ef4444' }}
              />
              <ReferenceLine
                y={2}
                stroke="#f59e0b"
                strokeDasharray="5 5"
                label={{ value: 'Warning Zone', fill: '#f59e0b' }}
              />
              <Area
                type="monotone"
                dataKey="dd"
                stroke="#ef4444"
                strokeWidth={3}
                fill="url(#ddGradient)"
                animationDuration={2000}
                style={{
                  filter: 'drop-shadow(0px 0px 8px rgba(239, 68, 68, 0.6))',
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-12"
        >
          <h2 className="text-2xl font-bold mb-8">📅 Event Timeline</h2>

          <div className="space-y-6">
            {caseStudy.timeline.map((event: any, idx: number) => {
              const isCollapse = event.dd === null;
              const isWarning = event.dd !== null && event.dd < 2 && event.dd >= 0;
              const isCritical = event.dd !== null && event.dd < 0;

              let borderColor = 'border-zinc-700';
              let bgColor = 'bg-zinc-900';

              if (isCollapse) {
                borderColor = 'border-red-500';
                bgColor = 'bg-red-500/10';
              } else if (isCritical) {
                borderColor = 'border-orange-500';
                bgColor = 'bg-orange-500/10';
              } else if (isWarning) {
                borderColor = 'border-yellow-500';
                bgColor = 'bg-yellow-500/10';
              }

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.05 * idx }}
                  className={`${bgColor} border-2 ${borderColor} rounded-2xl p-6`}
                >
                  <div className="flex items-start gap-6">
                    <div className="flex-shrink-0 text-center">
                      <div className="text-2xl mb-2">{event.signalStrength}</div>
                      <div className="text-sm font-bold text-white">{event.label}</div>
                      {event.dd !== null && (
                        <div className="text-xs text-zinc-400 mt-1">DD: {event.dd}σ</div>
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          event.signal === 'NEUTRAL' ? 'bg-zinc-700 text-zinc-300' :
                          event.signal === 'SHORT CREDIT' ? 'bg-red-500/20 text-red-400' :
                          'bg-red-600 text-white'
                        }`}>
                          {event.signal}
                        </span>
                        {event.spread_diff !== null && (
                          <span className="text-sm text-zinc-400">
                            Spread Diff: <span className="text-white font-medium">{event.spread_diff > 0 ? '+' : ''}{event.spread_diff} bps</span>
                          </span>
                        )}
                      </div>
                      <p className="text-white">{event.event}</p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Key Learnings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8"
        >
          <h2 className="text-2xl font-bold mb-6">💡 Key Learnings</h2>
          <ul className="space-y-4">
            {caseStudy.learnings.map((learning: string, idx: number) => (
              <motion.li
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.45 + idx * 0.05 }}
                className="flex items-start gap-3"
              >
                <span className="text-emerald-400 text-xl">✓</span>
                <span className="text-zinc-300">{learning}</span>
              </motion.li>
            ))}
          </ul>
        </motion.div>
      </main>
    </div>
  );
}