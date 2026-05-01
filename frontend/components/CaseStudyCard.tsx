'use client';

import { ArrowRight, Activity } from 'lucide-react';

interface CaseStudy {
  id: string;
  icon: string;
  title: string;
  subtitle: string;
  summary: string;
  outcome: string;
  date: string;
  severityColor: string;
}

interface CaseStudyCardProps {
  caseStudy: CaseStudy;
  onClick: () => void;
}

const getSeverityStyles = (color: string) => {
  // Severity indicated by a persistent top border and subtle terminal badge
  const styles: Record<string, { topBorder: string; badgeText: string; badgeBg: string }> = {
    red: { topBorder: 'border-t-red-600', badgeText: 'text-red-400', badgeBg: 'bg-red-950/30 border-red-900/50' },
    orange: { topBorder: 'border-t-orange-500', badgeText: 'text-orange-400', badgeBg: 'bg-orange-950/30 border-orange-900/50' },
    yellow: { topBorder: 'border-t-amber-500', badgeText: 'text-amber-400', badgeBg: 'bg-amber-950/30 border-amber-900/50' },
  };
  return styles[color] || { topBorder: 'border-t-zinc-700', badgeText: 'text-zinc-400', badgeBg: 'bg-zinc-900 border-zinc-800' };
};

export default function CaseStudyCard({ caseStudy, onClick }: CaseStudyCardProps) {
  const sev = getSeverityStyles(caseStudy.severityColor);

  return (
    <div
      onClick={onClick}
      className={`group cursor-pointer p-6 md:p-8 bg-zinc-950 border border-zinc-900 transition-all duration-500 relative overflow-hidden border-t-[3px] ${sev.topBorder} hover:shadow-[0_0_40px_rgba(255,255,255,0.03)]`}
    >
      {/* ── Subsurface Light Blur ── */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.06),transparent_50%)] transition-opacity duration-700 pointer-events-none" />

      <div className="relative z-10 flex flex-col h-full justify-between">
        <div>
          {/* ── Data Node Header ── */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="px-2.5 py-1 border border-zinc-800 bg-black text-white font-mono text-[10px] tracking-widest font-bold group-hover:border-zinc-500 transition-colors">
                {caseStudy.icon}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-zinc-500 font-mono">
                {caseStudy.date}
              </div>
            </div>
            <Activity size={16} className="text-zinc-700 group-hover:text-white transition-colors duration-500" />
          </div>

          {/* ── Core Identifiers ── */}
          <h3 className="text-2xl md:text-3xl font-serif text-zinc-100 tracking-tight mb-3 group-hover:translate-x-1 transition-transform duration-300">
            {caseStudy.title}
          </h3>

          <p className="text-[10px] uppercase tracking-widest text-zinc-500 font-mono mb-6 border-b border-zinc-900 pb-4">
            {caseStudy.subtitle}
          </p>

          <p className="text-zinc-400 text-sm leading-relaxed font-sans mb-8">
            {caseStudy.summary}
          </p>
        </div>

        {/* ── Action Footer ── */}
        <div className="flex items-center justify-between pt-5 border-t border-zinc-900 group-hover:border-zinc-700 transition-colors overflow-hidden">
          <span className={`text-[10px] uppercase tracking-widest font-mono px-2 py-1 border ${sev.badgeBg} ${sev.badgeText}`}>
            {caseStudy.outcome}
          </span>
          <div className="flex items-center text-[10px] uppercase tracking-widest font-mono font-bold text-white opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
            <span>Terminal Trace</span>
            <ArrowRight size={12} className="ml-2" />
          </div>
        </div>
      </div>
    </div>
  );
}