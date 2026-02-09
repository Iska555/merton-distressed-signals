'use client';

import { motion } from 'framer-motion';
import { Layers } from 'lucide-react';

export default function EmptyWatchlist() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-32 border border-dashed border-zinc-900 bg-zinc-950/20"
    >
      <div className="p-4 bg-zinc-900 mb-6 border border-zinc-800">
        <Layers size={24} className="text-zinc-500" strokeWidth={1} />
      </div>

      <h3 className="text-xl font-serif text-white tracking-wide mb-3">
        Portfolio Empty
      </h3>
      
      <p className="text-[10px] text-zinc-600 uppercase tracking-[0.3em] max-w-xs text-center leading-loose">
        No institutional credit entities currently being monitored. 
        Use the input above to initialize tracking.
      </p>
    </motion.div>
  );
}