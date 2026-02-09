'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, TrendingDown, Calendar, ArrowLeft, Target, ShieldCheck, Zap } from 'lucide-react';
import CaseStudyCard from '@/components/CaseStudyCard';
import CaseStudyDetail from '@/components/CaseStudyDetail';

// Keep your existing data structure, just restyling the UI
const caseStudies = [
  {
    id: 'svb',
    icon: '🏦',
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
        event: '🚨 STRONG SIGNAL: Model detects severe credit deterioration. Theoretical spread jumps to 650 bps while bonds still trading at 180 bps.',
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
        signalStrength: '💀',
        event: '🏦 FDIC seizes Silicon Valley Bank. 16th largest bank failure in US history.',
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
      'Traditional credit ratings were too slow - still rated investment grade on March 8',
      'Model would have given traders 2-week head start to exit positions',
    ],
  },
  {
    id: 'bbby',
    icon: '🛏️',
    title: 'Bed Bath & Beyond',
    subtitle: '2022-2023 Bankruptcy',
    date: 'April 23, 2023',
    summary: 'Model predicted distress 6 months before bankruptcy filing',
    outcome: 'BANKRUPTCY',
    severityColor: 'orange',
    timeline: [
      {
        date: '2022-10-15',
        label: 'Oct 2022',
        dd: 4.1,
        signal: 'NEUTRAL',
        signalStrength: '★',
        event: 'Stock price declining but still above $5. Equity volatility elevated at 85%.',
        spread_diff: 65,
      },
      {
        date: '2022-11-15',
        label: 'Nov 2022',
        dd: 2.8,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★',
        event: 'Distance to Default falling. Theoretical spread at 420 bps vs market 240 bps.',
        spread_diff: 180,
      },
      {
        date: '2022-12-15',
        label: 'Dec 2022',
        dd: 1.5,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★',
        event: 'Stock below $2. Model shows severe distress. Spread difference widens to 380 bps.',
        spread_diff: 380,
      },
      {
        date: '2023-01-15',
        label: 'Jan 2023',
        dd: 0.7,
        signal: 'SHORT CREDIT',
        signalStrength: '★★★★★',
        event: 'Distance to Default approaching zero. Default probability >35%.',
        spread_diff: 520,
      },
      {
        date: '2023-04-23',
        label: 'Apr 23',
        dd: null,
        signal: 'BANKRUPTCY',
        signalStrength: '💀',
        event: '🛏️ Files for Chapter 11 bankruptcy. All stores to close.',
        spread_diff: null,
      },
    ],
    metrics: {
      leadTime: '6 months',
      maxDD: 4.1,
      minDD: 0.7,
      signalAccuracy: '100%',
      peakSpreadDiff: 520,
    },
    learnings: [
      'Gradual deterioration visible 6 months before bankruptcy',
      'High equity volatility (>80%) was early warning sign',
      'Bond market remained complacent until final month',
      'Systematic shorting of credit would have been highly profitable',
    ],
  },
  {
    id: 'wework',
    icon: '🏢',
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
        event: '🏢 IPO cancelled. CEO ousted. Valuation crashes to $8B.',
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
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <main className="container mx-auto px-6 py-12 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-serif mb-4 tracking-tight">
            Predictive Validation
          </h2>
          <p className="text-zinc-500 font-sans tracking-wide text-xs max-w-2xl mx-auto uppercase leading-loose">
            Historical backtesting of the Merton model against major corporate solvency events.
          </p>
        </motion.div>

        {/* Stats Banner - Monochrome Institutional Look */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-0 border-y border-zinc-800 mb-16"
        >
          <div className="p-8 text-center border-b md:border-b-0 md:border-r border-zinc-800">
            <div className="text-4xl font-serif text-white mb-2">100%</div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-500">Signal Accuracy</div>
          </div>
          <div className="p-8 text-center border-b md:border-b-0 md:border-r border-zinc-800">
            <div className="text-4xl font-serif text-white mb-2">2-24</div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-500">Weeks Early Warning</div>
          </div>
          <div className="p-8 text-center">
            <div className="text-4xl font-serif text-white mb-2">3</div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-500">Major Events</div>
          </div>
        </motion.div>

        {/* Case Study Cards */}
        <div className="space-y-4 max-w-4xl mx-auto">
          {caseStudies.map((study, idx) => (
            <motion.div
              key={study.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * idx }}
            >
              <CaseStudyCard
                caseStudy={study}
                onClick={() => setSelectedCase(study.id)}
              />
            </motion.div>
          ))}
        </div>

        {/* Methodology Note */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-20 border-t border-zinc-900 pt-8 max-w-4xl mx-auto"
        >
          <h3 className="text-sm font-serif font-bold mb-4 flex items-center gap-2 uppercase tracking-widest text-zinc-400">
            Methodology Note
          </h3>
          <div className="text-zinc-500 space-y-3 text-[11px] leading-relaxed tracking-wide font-mono">
            <p>
              Calculations utilize historical equity data to simulate real-time Merton model outputs. 
              Distance to Default (DD) derived from market cap, total debt, and 60-day realized equity volatility.
            </p>
            <p>
              Theoretical spreads compared against historical market credit spreads or rating-tier indices where direct data is unavailable.
            </p>
          </div>
        </motion.div>
      </main>
    </div>
  );
}