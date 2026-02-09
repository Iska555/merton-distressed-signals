'use client';

import { motion } from 'framer-motion';
import { ArrowLeft, Target, ShieldCheck, Zap } from 'lucide-react';

interface CaseStudyDetailProps {
  caseStudy: any;
  onBack: () => void;
}

export default function CaseStudyDetail({ caseStudy, onBack }: CaseStudyDetailProps) {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* NO HEADER HERE - Layout handles it */}
      
      <main className="container mx-auto px-6 py-12 max-w-5xl">
        {/* Local Navigation / Breadcrumb */}
        <div className="mb-8 flex items-center gap-4">
           <button onClick={onBack} className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-zinc-500 hover:text-white transition-colors">
             <ArrowLeft size={14} />
             Back to Index
           </button>
           <div className="h-4 w-px bg-zinc-800" />
           <span className="text-[10px] uppercase tracking-widest text-white">{caseStudy.title}</span>
        </div>

        {/* Title Section */}
        <div className="mb-12 border-b border-zinc-800 pb-8">
           <h1 className="text-4xl font-serif mb-2">{caseStudy.title} Event Log</h1>
           <div className="flex gap-4 text-xs text-zinc-500 font-mono">
              <span>DATE: {caseStudy.date}</span>
              <span>OUTCOME: {caseStudy.outcome}</span>
           </div>
        </div>

        {/* Metric Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-zinc-900 border border-zinc-900 mb-16">
          {Object.entries(caseStudy.metrics).map(([key, value]: any) => (
            <div key={key} className="bg-black p-6 hover:bg-zinc-950 transition-colors">
              <p className="text-zinc-600 text-[9px] uppercase tracking-widest mb-2">{key.replace(/([A-Z])/g, ' $1')}</p>
              <p className="text-xl font-serif text-white">{value}</p>
            </div>
          ))}
        </div>

        {/* Timeline - Institutional Style */}
        <div className="mb-16">
          <h2 className="text-lg font-serif mb-8 border-l-2 border-white pl-4">Model Signal Timeline</h2>
          <div className="space-y-0">
            {caseStudy.timeline.map((item: any, idx: number) => (
              <div key={idx} className="relative pl-8 pb-8 border-l border-zinc-800 last:border-0 group">
                {/* Dot */}
                <div className={`absolute left-[-5px] top-0 w-2.5 h-2.5 rounded-full border-2 border-black ${item.signal === 'SHORT CREDIT' ? 'bg-white' : 'bg-zinc-800 group-hover:bg-zinc-600'}`} />
                
                <div className="grid md:grid-cols-4 gap-4">
                   <div className="md:col-span-1">
                      <p className="text-xs font-mono text-zinc-500">{item.date}</p>
                      <p className="text-[10px] uppercase tracking-widest text-zinc-600 mt-1">DD: {item.dd ?? 'N/A'}</p>
                   </div>
                   <div className="md:col-span-3">
                      <div className="flex items-center gap-3 mb-2">
                         <span className={`text-xs font-bold uppercase tracking-wider ${item.signal === 'SHORT CREDIT' ? 'text-white' : 'text-zinc-500'}`}>
                           {item.signal}
                         </span>
                         <span className="text-xs tracking-tighter text-zinc-600">{item.signalStrength}</span>
                      </div>
                      <p className="text-sm text-zinc-400 font-serif leading-relaxed border-l border-zinc-900 pl-4">
                        {item.event}
                      </p>
                   </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Learnings */}
        <div className="bg-zinc-950 border border-zinc-900 p-8">
          <h3 className="text-sm font-bold uppercase tracking-widest mb-6 flex items-center gap-2 text-zinc-400">
            <Zap size={14} /> Quantitative Insights
          </h3>
          <ul className="grid md:grid-cols-2 gap-6">
            {caseStudy.learnings.map((learning: string, i: number) => (
              <li key={i} className="flex gap-4 text-zinc-400 text-xs leading-loose">
                <ShieldCheck className="text-zinc-600 shrink-0 mt-0.5" size={14} />
                {learning}
              </li>
            ))}
          </ul>
        </div>
      </main>
    </div>
  );
}