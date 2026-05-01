'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { MertonEventResult } from '@/lib/api';
import EventCard from './EventCard';

interface Props {
  results: MertonEventResult[];
}

const COLUMNS = [
  { label: 'Ticker',   cls: 'w-24'  },
  { label: 'Signal',   cls: 'w-36'  },
  { label: 'Theo Spd', cls: 'w-28'  },
  { label: 'Mkt Spd',  cls: 'w-28'  },
  { label: 'α Gap',    cls: 'w-28'  },
  { label: 'DD (σ)',   cls: 'w-20'  },
  { label: 'PD %',     cls: 'w-20'  },
  { label: 'Trigger',  cls: 'w-28'  },
  { label: 'ΔPrice',   cls: 'w-24'  },
];

export default function EventFeed({ results }: Props) {
  if (results.length === 0) {
    return (
      <div className="border border-zinc-800 bg-black py-24 flex items-center justify-center">
        <p className="text-[11px] text-zinc-700 uppercase tracking-widest font-mono">
          No signals match current filter
        </p>
      </div>
    );
  }

  return (
    <div className="border border-zinc-800 bg-black overflow-x-auto">

      {/* Column headers */}
      <div className="flex items-center gap-4 px-4 py-2.5 border-b border-zinc-900 min-w-max bg-zinc-950/50">
        {COLUMNS.map(col => (
          <span
            key={col.label}
            className={`${col.cls} text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-mono`}
          >
            {col.label}
          </span>
        ))}
        <span className="flex-1 text-[9px] text-zinc-600 uppercase tracking-[0.2em] font-mono text-right pr-6">
          Company
        </span>
      </div>

      {/* Rows */}
      <AnimatePresence mode="popLayout" initial={false}>
        {results.map((result, i) => (
          <motion.div
            key={`${result.ticker}-${result.scan_timestamp}`}
            layout
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18, delay: i * 0.03 }}
          >
            <EventCard result={result} />
          </motion.div>
        ))}
      </AnimatePresence>

    </div>
  );
}