'use client';

import { motion } from 'framer-motion';
import { TrendingDown, Calendar, ArrowRight } from 'lucide-react';

interface CaseStudyCardProps {
  caseStudy: any;
  onClick: () => void;
}

export default function CaseStudyCard({ caseStudy, onClick }: CaseStudyCardProps) {
  return (
    <motion.div
      whileHover={{ x: 10 }}
      onClick={onClick}
      className="group cursor-pointer bg-zinc-950 border border-zinc-900 hover:border-zinc-700 p-8 transition-all border-l-2 border-l-zinc-800 hover:border-l-white"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start gap-6">
          <div className="text-3xl grayscale group-hover:grayscale-0 transition-all opacity-70">
            {caseStudy.icon}
          </div>
          <div>
            <h3 className="text-xl font-serif font-bold text-white mb-1 tracking-wide">{caseStudy.title}</h3>
            <p className="text-[10px] text-zinc-500 uppercase tracking-widest">{caseStudy.subtitle}</p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
           <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-zinc-400">
             <span>{caseStudy.outcome}</span>
             <span className="w-1 h-1 bg-zinc-600 rounded-full"/>
             <span>{caseStudy.date}</span>
           </div>
           <div className="flex items-center gap-2 text-zinc-500 group-hover:text-white transition-colors">
             <span className="text-xs font-serif italic">View Analysis</span>
             <ArrowRight size={14} />
           </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-zinc-900 flex items-start gap-3">
        <TrendingDown className="text-zinc-600 mt-0.5" size={16} />
        <p className="text-zinc-400 text-sm font-serif italic leading-relaxed">"{caseStudy.summary}"</p>
      </div>
    </motion.div>
  );
}