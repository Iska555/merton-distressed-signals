'use client';

import { motion } from 'framer-motion';
import { ChevronRight } from 'lucide-react';

interface CaseStudyCardProps {
  caseStudy: {
    id: string;
    icon: string;
    title: string;
    subtitle: string;
    date: string;
    summary: string;
    outcome: string;
    severityColor: string;
    metrics: {
      leadTime: string;
      signalAccuracy: string;
    };
  };
  onClick: () => void;
}

export default function CaseStudyCard({ caseStudy, onClick }: CaseStudyCardProps) {
  const severityColors = {
    red: 'from-red-500/20 to-orange-500/20 border-red-500/50',
    orange: 'from-orange-500/20 to-yellow-500/20 border-orange-500/50',
    yellow: 'from-yellow-500/20 to-amber-500/20 border-yellow-500/50',
  };

  const bgGradient = severityColors[caseStudy.severityColor as keyof typeof severityColors];

  return (
    <motion.div
      whileHover={{ scale: 1.02, x: 10 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`bg-gradient-to-br ${bgGradient} border-2 rounded-3xl p-8 cursor-pointer transition-all`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-4">
            <div className="text-6xl">{caseStudy.icon}</div>
            <div>
              <h3 className="text-2xl font-bold text-white mb-1">{caseStudy.title}</h3>
              <p className="text-zinc-400">{caseStudy.subtitle}</p>
            </div>
          </div>

          <p className="text-lg text-white mb-6">{caseStudy.summary}</p>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-zinc-500 mb-1">Date</p>
              <p className="text-sm font-medium text-white">{caseStudy.date}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 mb-1">Lead Time</p>
              <p className="text-sm font-medium text-emerald-400">{caseStudy.metrics.leadTime}</p>
            </div>
            <div>
              <p className="text-xs text-zinc-500 mb-1">Accuracy</p>
              <p className="text-sm font-medium text-emerald-400">{caseStudy.metrics.signalAccuracy}</p>
            </div>
          </div>

          <div className="mt-6 inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors">
            View Full Timeline
            <ChevronRight size={16} />
          </div>
        </div>
      </div>
    </motion.div>
  );
}