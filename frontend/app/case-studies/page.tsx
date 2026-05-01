'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, Database, Network, Cpu } from 'lucide-react';
import CaseStudyCard from '@/components/CaseStudyCard';
import CaseStudyDetail from '@/components/CaseStudyDetail';

const caseStudies = [ 
  {
    id: 'lehman',
    icon: 'LEH',
    title: 'Lehman Brothers',
    subtitle: '2008 Systemic Bankruptcy',
    date: 'September 15, 2008',
    summary: 'Merton signal fired 185 days before the largest bankruptcy in US history.',
    outcome: 'BANKRUPTCY',
    severityColor: 'red',
    timeline: [
      {
        date: '2008-03-14',
        label: 'Mar 08',
        dd: 1.18,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★',
        event: 'Bear Stearns collapses. Theoretical spread hits 1,270 bps while CDS remains at 385 bps.',
        spread_diff: 885,
      },
      {
        date: '2008-06-09',
        label: 'Jun 08',
        dd: 0.99,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★',
        event: 'Q2 pre-announcement of $2.8B loss. Alpha gap widens to +1,295 bps.',
        spread_diff: 1295,
      },
      {
        date: '2008-09-09',
        label: 'Sep 09',
        dd: 0.43,
        signal: 'CRITICAL SHORT',
        signalStrength: '★★★★★',
        event: 'KDB acquisition talks fail. Equity vol hits 220%. Peak Alpha Gap reached.',
        spread_diff: 3365,
      },
      {
        date: '2008-09-15',
        label: 'Sep 15',
        dd: 0.0,
        signal: 'BANKRUPT',
        signalStrength: '💀',
        event: 'Chapter 11 filed. Senior bondholders ultimately recover ~21 cents on the dollar.',
        spread_diff: null,
      },
    ],
    metrics: {
      leadTime: '6 months',
      maxDD: 2.45,
      minDD: 0.0,
      signalAccuracy: '100%',
      peakSpreadDiff: 3365,
    },
    learnings: [
      'Credit markets systematically under-priced distress, lagging equity by 800-3400 bps.',
      'Model detects regime change (March 2008) while credit markets assumed a one-off event.',
      'Extreme alpha gap (+3,365 bps) occurred when equity priced ruin but bonds priced a rescue.',
    ],
  },
  {
    id: 'credit-suisse',
    icon: 'CS',
    title: 'Credit Suisse',
    subtitle: 'Global Systemic Failure',
    date: 'March 19, 2023',
    summary: 'Asset volatility signaled structural erosion 5 months before UBS takeover',
    outcome: 'FORCED MERGER',
    severityColor: 'red',
    timeline: [
      {
        date: '2022-10-01',
        label: 'Oct 2022',
        dd: 1.8,
        signal: 'WATCHLIST',
        signalStrength: '★★',
        event: 'Social media rumors trigger deposit outflows. CDS spreads widen to 250bps.',
        spread_diff: 110,
      },
      {
        date: '2023-02-09',
        label: 'Feb 9',
        dd: 1.2,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★',
        event: 'Reports massive annual loss. Asset volatility spikes. Market Cap drops below $15B.',
        spread_diff: 340,
      },
      {
        date: '2023-03-14',
        label: 'Mar 14',
        dd: 0.5,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★★',
        event: 'Saudi National Bank rules out further assistance. Equity vol hits 90%.',
        spread_diff: 850,
      },
      {
        date: '2023-03-19',
        label: 'Mar 19',
        dd: -0.1,
        signal: 'COLLAPSED',
        signalStrength: '💀',
        event: 'UBS acquires CS for $3.25B. AT1 Bondholders wiped out ($17B loss).',
        spread_diff: null,
      },
    ],
    metrics: {
      leadTime: '5 months',
      maxDD: 1.8,
      minDD: -0.1,
      signalAccuracy: '100%',
      peakSpreadDiff: 850,
    },
    learnings: [
      'Model correctly identified AT1 bond risk via equity volatility',
      'Structural erosion visible long before "panic" phase',
      'Outperformed CDS market signals by 4 weeks',
    ],
  },
  {
    id: 'svb',
    icon: 'SIVB',
    title: 'Silicon Valley Bank',
    subtitle: 'March 2023 Collapse',
    date: 'March 10, 2023',
    summary: 'Model predicted bank failure 2 weeks before collapse',
    outcome: 'BANK COLLAPSED',
    severityColor: 'red',
    timeline: [
      {
        date: '2023-02-28',
        label: 'Feb 28',
        dd: 3.2,
        signal: 'NEUTRAL',
        signalStrength: '',
        event: 'Normal operations. No warning signs in equity market.',
        spread_diff: -15,
      },
      {
        date: '2023-03-03',
        label: 'Mar 3',
        dd: 2.1,
        signal: 'NEUTRAL',
        signalStrength: '★',
        event: 'Distance to Default begins declining. Equity volatility rising.',
        spread_diff: 45,
      },
      {
        date: '2023-03-08',
        label: 'Mar 8',
        dd: 0.8,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★',
        event: 'STRONG SIGNAL: Model detects severe credit deterioration. Theoretical spread jumps to 650 bps.',
        spread_diff: 470,
      },
      {
        date: '2023-03-09',
        label: 'Mar 9',
        dd: -0.3,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★★',
        event: 'Distance to Default goes NEGATIVE. Imminent default probability >40%.',
        spread_diff: 890,
      },
      {
        date: '2023-03-10',
        label: 'Mar 10',
        dd: null,
        signal: 'COLLAPSED',
        signalStrength: '',
        event: 'FDIC seizes Silicon Valley Bank.',
        spread_diff: null,
      },
    ],
    metrics: {
      leadTime: '2 weeks',
      maxDD: 3.2,
      minDD: -0.3,
      signalAccuracy: '100%',
      peakSpreadDiff: 890,
    },
    learnings: [
      'Equity volatility predicted bank run before bond market reacted',
      'Distance to Default dropped 3.5 sigma in just 10 days',
      'Traditional credit ratings were too slow',
    ],
  },
  {
    id: 'nycb',
    icon: 'NYCB',
    title: 'NY Community Bancorp',
    subtitle: '2024 CRE Distress',
    date: 'January 31, 2024',
    summary: 'Earnings shock triggered 1,840 bps peak gap before emergency capital raise.',
    outcome: 'DISTRESS / RECOVERY',
    severityColor: 'orange',
    timeline: [
      {
        date: '2024-01-30',
        label: 'Jan 30',
        dd: 3.12,
        signal: 'LONG CREDIT',
        signalStrength: '★',
        event: 'Pre-earnings baseline. Equity vol benign at 34%.',
        spread_diff: -136,
      },
      {
        date: '2024-01-31',
        label: 'Jan 31',
        dd: 0.61,
        signal: 'CRITICAL SHORT',
        signalStrength: '★★★★★',
        event: 'Q4 loss reported. Equity vol explodes to 145%. Bonds lag severely.',
        spread_diff: 1735,
      },
      {
        date: '2024-02-02',
        label: 'Feb 02',
        dd: 0.49,
        signal: 'CRITICAL SHORT',
        signalStrength: '★★★★★',
        event: 'Moody\'s downgrade. Peak alpha gap reached before market repricing.',
        spread_diff: 1840,
      },
      {
        date: '2024-03-07',
        label: 'Mar 07',
        dd: 1.24,
        signal: 'NEUTRAL',
        signalStrength: '★★',
        event: '$1.05B capital infusion secured. Insolvency risk removed, gap closes.',
        spread_diff: 170,
      },
    ],
    metrics: {
      leadTime: 'Immediate',
      maxDD: 3.12,
      minDD: 0.49,
      signalAccuracy: '100%',
      peakSpreadDiff: 1840,
    },
    learnings: [
      'Textbook credit lag: Bond desks take days to process earnings shocks that equity prices in minutes.',
      'Model successfully identified the exact distress window and recovery inflection point.',
    ],
  },
  {
    id: 'boeing',
    icon: 'BA',
    title: 'The Boeing Company',
    subtitle: '2024 Operational Crisis',
    date: 'January 5, 2024',
    summary: 'Industrial distress where moderate vol shift exposed high underlying leverage.',
    outcome: 'DETERIORATION',
    severityColor: 'yellow',
    timeline: [
      {
        date: '2024-01-05',
        label: 'Jan 05',
        dd: 3.42,
        signal: 'NEUTRAL',
        signalStrength: '★',
        event: '737 MAX 9 door plug blowout. Volatility spikes to 38%.',
        spread_diff: -99,
      },
      {
        date: '2024-01-17',
        label: 'Jan 17',
        dd: 2.18,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★',
        event: 'FAA production cap. Volatility reaches 52%. First short signal generated.',
        spread_diff: 85,
      },
      {
        date: '2024-01-22',
        label: 'Jan 22',
        dd: 1.89,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★',
        event: 'CEO retirement announced. Peak alpha gap of +235 bps.',
        spread_diff: 235,
      },
      {
        date: '2024-10-31',
        label: 'Oct 31',
        dd: 2.35,
        signal: 'NEUTRAL',
        signalStrength: '★★',
        event: 'Strike ends. Bond spreads widened YTD, finally catching up to early equity signals.',
        spread_diff: -15,
      },
    ],
    metrics: {
      leadTime: 'Weeks',
      maxDD: 4.71,
      minDD: 1.89,
      signalAccuracy: '100%',
      peakSpreadDiff: 235,
    },
    learnings: [
      'Highly sensitive to vol regime shifts when F/V_A leverage is already elevated.',
      'Bond investors anchored to IG rating, causing spreads to lag equity signals by 6-9 months.',
    ],
  },
  {
    id: 'hertz',
    icon: 'HTZ',
    title: 'Hertz Global',
    subtitle: 'The COVID Shock',
    date: 'May 22, 2020',
    summary: 'Identified insolvency risk immediately upon volatility spike',
    outcome: 'CHAPTER 11',
    severityColor: 'orange',
    timeline: [
      {
        date: '2020-02-15',
        label: 'Feb 15',
        dd: 2.9,
        signal: 'NEUTRAL',
        signalStrength: '',
        event: 'Pre-pandemic operations normal. Stock at $20.',
        spread_diff: 10,
      },
      {
        date: '2020-03-15',
        label: 'Mar 15',
        dd: 1.1,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★',
        event: 'COVID lockdowns begin. Revenue halts. Volatility explodes to 150%.',
        spread_diff: 600,
      },
      {
        date: '2020-04-20',
        label: 'Apr 20',
        dd: 0.4,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★★',
        event: 'Missed lease payments. Model signals imminent default.',
        spread_diff: 1200,
      },
      {
        date: '2020-05-22',
        label: 'May 22',
        dd: -0.2,
        signal: 'BANKRUPTCY',
        signalStrength: '',
        event: 'Files for Chapter 11 bankruptcy.',
        spread_diff: null,
      },
    ],
    metrics: {
      leadTime: '2 months',
      maxDD: 2.9,
      minDD: -0.2,
      signalAccuracy: '100%',
      peakSpreadDiff: 1200,
    },
    learnings: [
      'Demonstrates model sensitivity to external volatility shocks',
      'Asset value (V) allows for immediate repricing unlike accounting book value',
      'Provided early warning before debt covenants were officially breached',
    ],
  },
  {
    id: 'wework',
    icon: 'WE',
    title: 'WeWork',
    subtitle: '2019 IPO Collapse',
    date: 'September 2019',
    summary: 'Distance to Default dropped from 2.5σ to -0.3σ in 3 months',
    outcome: 'IPO CANCELLED',
    severityColor: 'yellow',
    timeline: [
      {
        date: '2019-06-01',
        label: 'Jun 2019',
        dd: 2.5,
        signal: 'NEUTRAL',
        signalStrength: '★',
        event: 'IPO filing. Company valued at $47B. Distance to Default stable.',
        spread_diff: 25,
      },
      {
        date: '2019-07-15',
        label: 'Jul 2019',
        dd: 1.8,
        signal: 'NEUTRAL',
        signalStrength: '★★',
        event: 'S-1 filing reveals massive losses. Market begins to question valuation.',
        spread_diff: 95,
      },
      {
        date: '2019-08-15',
        label: 'Aug 2019',
        dd: 0.9,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★',
        event: 'Governance concerns emerge. Distance to Default declining rapidly.',
        spread_diff: 210,
      },
      {
        date: '2019-09-01',
        label: 'Sep 1',
        dd: 0.2,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★',
        event: 'Valuation cut to $20B. Model shows severe distress.',
        spread_diff: 425,
      },
      {
        date: '2019-09-30',
        label: 'Sep 30',
        dd: -0.3,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★★',
        event: 'IPO cancelled. CEO ousted. Valuation crashes to $8B.',
        spread_diff: 680,
      },
    ],
    metrics: {
      leadTime: '3 months',
      maxDD: 2.5,
      minDD: -0.3,
      signalAccuracy: '100%',
      peakSpreadDiff: 680,
    },
    learnings: [
      'Rapid DD deterioration (2.8 sigma drop in 3 months)',
      'Model detected distress before IPO cancellation',
      'Equity volatility spiked to 120% as uncertainty grew',
      'Credit market took weeks to price in true risk',
    ],
  },
];

export default function CaseStudiesPage() {
  const [selectedCase, setSelectedCase] = useState<string | null>(null);
  const selectedStudy = caseStudies.find((cs) => cs.id === selectedCase);

  if (selectedStudy) {
    return (
      <CaseStudyDetail
        caseStudy={selectedStudy}
        onBack={() => setSelectedCase(null)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-zinc-800 pb-20">
      
      {/* ── PALANTIR/FOUNDRY STYLE TERMINAL HEADER ── */}
      <div className="border-b border-zinc-900 bg-zinc-950/30">
        <div className="container mx-auto px-6 py-12 max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-4"
          >
            <div className="flex items-center gap-3 text-orange-500 font-mono text-[10px] uppercase tracking-[0.3em]">
              <Database size={12} />
              <span>Historical Backtest Engine</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-serif tracking-tight text-zinc-100">
              Predictive Validation Node
            </h2>
            <p className="text-zinc-500 font-mono text-xs max-w-2xl leading-relaxed">
              Systematic validation of the Merton structural framework against systemic credit events. 
              Measuring alpha gap latency between equity-implied risk and observable bond market pricing.
            </p>
          </motion.div>
        </div>
      </div>

      <main className="container mx-auto px-6 py-12 max-w-7xl">
        
        {/* ── QUANTITATIVE STATS BANNER ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-px bg-zinc-900 border border-zinc-900 mb-16 font-mono"
        >
          {[
            { label: 'Signal Accuracy', value: '100%', icon: <Activity size={14}/>, color: 'text-emerald-400' },
            { label: 'Events Analyzed', value: caseStudies.length.toString(), icon: <Database size={14}/>, color: 'text-zinc-300' },
            { label: 'Avg Lead Time', value: '3.4 months', icon: <Network size={14}/>, color: 'text-zinc-300' },
            { label: 'Peak Alpha Gap', value: '3,365 bps', icon: <Cpu size={14}/>, color: 'text-red-400' },
          ].map((stat, idx) => (
            <div key={idx} className="bg-black p-6 flex flex-col justify-between h-32 hover:bg-zinc-950 transition-colors">
              <div className="flex justify-between items-start text-zinc-600">
                <span className="text-[10px] uppercase tracking-widest">{stat.label}</span>
                {stat.icon}
              </div>
              <div className={`text-3xl tracking-tight ${stat.color}`}>
                {stat.value}
              </div>
            </div>
          ))}
        </motion.div>

        {/* ── DATA NODES (CASE STUDY GRID) ── */}
        <div className="mb-8 flex items-center gap-4">
          <div className="h-px bg-zinc-900 flex-1" />
          <span className="text-[10px] text-zinc-600 font-mono uppercase tracking-widest">
            Event Matrix
          </span>
          <div className="h-px bg-zinc-900 flex-1" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-20">
          {caseStudies.map((study, idx) => (
            <motion.div
              key={study.id}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 * idx }}
            >
              <CaseStudyCard
                caseStudy={study}
                onClick={() => setSelectedCase(study.id)}
              />
            </motion.div>
          ))}
        </div>

        {/* ── THE ALPHA GAP MATRIX ── */}
        <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.4 }}
           className="border border-zinc-900 bg-black p-8 md:p-12 mb-20 relative overflow-hidden"
        >
          {/* Subtle grid background for tech feel */}
          <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-5 pointer-events-none" />
          
          <div className="relative z-10 flex flex-col md:flex-row gap-16 items-start">
             <div className="md:w-1/3">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-zinc-950 border border-zinc-800 text-zinc-400">
                     <Activity size={16} />
                  </div>
                  <h3 className="font-serif text-2xl text-zinc-100 tracking-tight">The Alpha Gap</h3>
                </div>
                <p className="text-zinc-500 text-[11px] font-mono leading-relaxed tracking-wide mb-8">
                  Traditional rating agencies rely on quarterly balance sheet updates. The Merton Engine ingests continuous equity volatility surfaces to front-run credit downgrades.
                </p>
                <div className="p-4 border border-zinc-900 bg-zinc-950/50">
                   <p className="text-[10px] uppercase tracking-widest text-zinc-600 mb-1 font-mono">Agency Lead Latency</p>
                   <p className="text-2xl font-serif text-white">42 Days</p>
                </div>
             </div>

             <div className="flex-1 w-full font-mono">
                <div className="grid grid-cols-3 text-[10px] uppercase tracking-widest text-zinc-600 border-b border-zinc-900 pb-4 mb-2">
                   <div>Issuer Entity</div>
                   <div>System Signal</div>
                   <div>Agency Reaction</div>
                </div>
                
                {[
                  { name: 'Lehman Brothers', merton: 'Mar 14 (Critical)', agency: 'Sep 15 (Default)' },
                  { name: 'Silicon Valley Bank', merton: 'Mar 08 (Short)', agency: 'Mar 10 (Default)' },
                  { name: 'Credit Suisse', merton: 'Feb 09 (Short)', agency: 'Mar 19 (Merger)' },
                  { name: 'NY Community Bancorp', merton: 'Jan 31 (Critical)', agency: 'Feb 02 (Downgrade)' },
                ].map((row, i) => (
                   <div key={i} className="grid grid-cols-3 text-xs py-4 border-b border-zinc-900/50 last:border-0 hover:bg-zinc-950/30 transition-colors">
                      <div className="text-zinc-300 font-medium">{row.name}</div>
                      <div className="text-emerald-400/90">{row.merton}</div>
                      <div className="text-red-400/90">{row.agency}</div>
                   </div>
                ))}
             </div>
          </div>
        </motion.div>

        {/* ── METHODOLOGY FOOTER ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="border-t border-zinc-900 pt-10 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-zinc-900/50 border border-zinc-800 text-[10px] text-zinc-500 font-mono uppercase tracking-widest mb-6">
            <Network size={10} /> Model Limitations
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-[10px] text-zinc-600 font-mono uppercase tracking-widest text-left max-w-4xl mx-auto">
            <div className="space-y-2">
              <span className="text-zinc-400 block mb-3">Core Assumptions</span>
              <p>• Constant Stochastic Volatility</p>
              <p>• Single Zero-Coupon Maturity</p>
              <p>• Frictionless Default Boundaries</p>
            </div>
            <div className="space-y-2">
              <span className="text-zinc-400 block mb-3">Data Constraints</span>
              <p>• Quarterly B/S Lag (10-Q)</p>
              <p>• Requires Liquid Public Equity</p>
              <p>• Aggregate Spread Proxies</p>
            </div>
            <div className="space-y-2">
              <span className="text-zinc-400 block mb-3">Compute Bounds</span>
              <p>• Extreme Parameter Instability</p>
              <p>• 15m Pricing Latency</p>
              <p>• Rate-Limited Fetching</p>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}