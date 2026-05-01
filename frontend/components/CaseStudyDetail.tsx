'use client';

import { motion } from 'framer-motion';
import { ArrowLeft, Activity, ShieldAlert, TrendingDown, Target } from 'lucide-react';

interface TimelineEvent {
  date: string;
  label: string;
  dd: number | null;
  signal: string;
  signalStrength: string;
  event: string;
  spread_diff: number | null;
}

interface CaseStudy {
  id: string;
  icon: string;
  title: string;
  subtitle: string;
  date: string;
  summary: string;
  outcome: string;
  severityColor: string;
  timeline: TimelineEvent[];
  metrics: {
    leadTime: string;
    maxDD: number;
    minDD: number;
    signalAccuracy: string;
    peakSpreadDiff: number;
  };
  learnings: string[];
}

interface Props {
  caseStudy: CaseStudy;
  onBack: () => void;
}

const getSeverityStyles = (color: string) => {
  const styles: Record<string, { text: string; bg: string; border: string; glow: string }> = {
    red: { text: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/20', glow: 'from-red-950/40' },
    orange: { text: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20', glow: 'from-orange-950/40' },
    yellow: { text: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/20', glow: 'from-yellow-950/40' },
  };
  return styles[color] || styles.red;
};

export default function CaseStudyDetail({ caseStudy, onBack }: Props) {
  const sev = getSeverityStyles(caseStudy.severityColor);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen bg-black text-zinc-300 font-sans selection:bg-zinc-800 pb-24"
    >
      {/* ── IMMERSIVE HERO NAVIGATION ── */}
      <div className={`relative border-b border-zinc-900 bg-gradient-to-b ${sev.glow} to-black overflow-hidden`}>
        {/* Abstract structural background */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10 mix-blend-overlay pointer-events-none" />
        
        <div className="container mx-auto px-6 max-w-7xl relative z-10">
          <div className="h-16 flex items-center justify-between border-b border-zinc-900/50 mb-12">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-zinc-500 hover:text-white transition-colors"
            >
              <ArrowLeft size={14} /> Back to Matrix
            </button>
            <div className="flex items-center gap-3">
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-600">
                Event Horizon
              </span>
              <span className={`px-2 py-1 text-[10px] font-mono uppercase tracking-widest border ${sev.bg} ${sev.text} ${sev.border}`}>
                {caseStudy.outcome}
              </span>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="max-w-4xl pb-16"
          >
            <div className="flex items-center gap-4 mb-6">
              <div className="w-14 h-14 border border-zinc-700 flex items-center justify-center bg-black shadow-2xl">
                <span className="font-mono text-sm tracking-widest text-white">{caseStudy.icon}</span>
              </div>
              <div>
                <h1 className="text-5xl md:text-6xl font-serif text-white tracking-tight mb-2">
                  {caseStudy.title}
                </h1>
                <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-zinc-500">
                  {caseStudy.subtitle} // {caseStudy.date}
                </p>
              </div>
            </div>
            <p className="text-xl md:text-2xl text-zinc-400 font-serif leading-relaxed max-w-3xl">
              {caseStudy.summary}
            </p>
          </motion.div>
        </div>
      </div>

      <main className="container mx-auto px-6 mt-[-40px] relative z-20 max-w-7xl">
        {/* ── METRICS GRID (Zero Dead Space) ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-2 md:grid-cols-5 gap-px bg-zinc-800 border border-zinc-800 mb-24 font-mono shadow-2xl"
        >
          {[
            { label: 'Warning Lead Time', value: caseStudy.metrics.leadTime, icon: <Activity size={14} /> },
            { label: 'Maximum Distance', value: `${caseStudy.metrics.maxDD}σ`, icon: <ShieldAlert size={14} /> },
            { label: 'Minimum Distance', value: `${caseStudy.metrics.minDD}σ`, icon: <TrendingDown size={14} /> },
            { label: 'Signal Accuracy', value: caseStudy.metrics.signalAccuracy, icon: <Target size={14} /> },
            { label: 'Peak Alpha Gap', value: `${caseStudy.metrics.peakSpreadDiff} bps`, icon: <Activity size={14} className={sev.text} />, highlight: true },
          ].map((stat, idx) => (
            <div 
              key={idx} 
              // The 5th item perfectly spans 2 columns on mobile, resolving the empty grid slot
              className={`bg-black p-6 flex flex-col justify-between h-36 hover:bg-zinc-950 transition-colors ${idx === 4 ? 'col-span-2 md:col-span-1' : ''}`}
            >
              <div className="flex justify-between items-start text-zinc-600">
                <span className="text-[10px] uppercase tracking-widest pr-4 leading-relaxed">{stat.label}</span>
                {stat.icon}
              </div>
              <div className={`text-3xl tracking-tight ${stat.highlight ? sev.text : 'text-white'}`}>
                {stat.value}
              </div>
            </div>
          ))}
        </motion.div>

        {/* ── EDITORIAL SPLIT (Log vs Learnings) ── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
          
          {/* LEFT: The Event Log Timeline */}
          <div className="lg:col-span-8">
            <div className="mb-10 border-b border-zinc-900 pb-4 flex items-center gap-3">
              <div className="w-2 h-2 bg-white rounded-full" />
              <h3 className="text-2xl font-serif text-white tracking-tight">Terminal Trace</h3>
            </div>
            
            <div className="relative border-l border-zinc-900 ml-4 md:ml-6 pb-8">
              {caseStudy.timeline.map((item, idx) => (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + idx * 0.1 }}
                  key={idx}
                  className="mb-14 relative pl-8 md:pl-12 group"
                >
                  {/* Glowing Node on Timeline */}
                  <div className={`absolute -left-[5px] top-1.5 w-[9px] h-[9px] rounded-full border border-black transition-all duration-300 ${item.signal.includes('SHORT') || item.signal === 'BANKRUPTCY' || item.signal === 'COLLAPSED' ? 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.8)]' : 'bg-zinc-600 group-hover:bg-zinc-400'}`} />
                  
                  <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-4 mb-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-white font-mono text-sm tracking-tight bg-zinc-900 px-2 py-1">{item.date}</span>
                        <span className={`px-2 py-1 text-[9px] font-mono uppercase tracking-widest border ${item.signal.includes('SHORT') || item.signal === 'BANKRUPTCY' ? 'text-red-400 border-red-900 bg-red-950/30' : 'text-zinc-400 border-zinc-800 bg-zinc-900'}`}>
                          {item.signal} {item.signalStrength}
                        </span>
                      </div>
                    </div>
                    {/* Immersive Data Node */}
                    <div className="flex gap-6 xl:text-right font-mono text-[11px] bg-zinc-950/50 p-3 border border-zinc-900/50">
                      <div>
                        <div className="text-zinc-600 uppercase tracking-widest mb-1">Dist to Def</div>
                        <div className="text-white text-sm">{item.dd !== null ? `${item.dd}σ` : 'N/A'}</div>
                      </div>
                      <div className="text-left xl:text-right min-w-[80px]">
                        <div className="text-zinc-600 uppercase tracking-widest mb-1">Spread Diff</div>
                        <div className={`text-sm ${item.spread_diff && item.spread_diff > 200 ? sev.text : 'text-white'}`}>
                          {item.spread_diff !== null ? `+${item.spread_diff} bps` : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-zinc-400 text-sm leading-relaxed border-l-2 border-zinc-800 pl-4 py-1">
                    {item.event}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* RIGHT: Analyst Debrief & Learnings */}
          <div className="lg:col-span-4">
            <div className="sticky top-24">
              <div className="border border-zinc-900 bg-black p-6 md:p-8 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-zinc-800 via-zinc-500 to-zinc-800 opacity-20" />
                
                <div className="flex items-center gap-3 mb-8 border-b border-zinc-900 pb-4">
                  <Activity size={16} className={sev.text} />
                  <h3 className="font-serif text-xl text-white">Structural Learnings</h3>
                </div>
                
                <ul className="space-y-8">
                  {caseStudy.learnings.map((learning, idx) => (
                    <motion.li
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 + idx * 0.1 }}
                      key={idx}
                      className="flex items-start gap-4 group"
                    >
                      <span className={`font-mono text-[10px] mt-1 px-1.5 border border-zinc-800 group-hover:border-zinc-500 transition-colors ${sev.text}`}>
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      <p className="text-zinc-400 text-xs font-mono leading-relaxed tracking-wide group-hover:text-zinc-300 transition-colors">
                        {learning}
                      </p>
                    </motion.li>
                  ))}
                </ul>

                <div className="mt-12 pt-6 border-t border-zinc-900">
                  <div className="text-[10px] uppercase tracking-widest text-zinc-600 font-mono mb-2">
                    System Directive
                  </div>
                  <p className="text-zinc-500 text-[11px] font-mono leading-relaxed">
                    This historically verified alpha gap forms the mathematical baseline for real-time arbitrage detection across modern credit structures.
                  </p>
                </div>
              </div>
            </div>
          </div>
          
        </div>
      </main>
    </motion.div>
  );
}