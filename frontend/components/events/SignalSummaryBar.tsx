'use client';

import { MertonEventResult, EventSignal } from '@/lib/api';
import { SignalFilter } from './EventScannerTerminal';

interface Props {
  results:  MertonEventResult[];
  filter:   SignalFilter;
  onFilter: (f: SignalFilter) => void;
}

const TABS: {
  key:         SignalFilter;
  label:       string;
  activeClass: string;
}[] = [
  { key: 'ALL',           label: 'All',           activeClass: 'text-white border-zinc-500 bg-zinc-950'      },
  { key: 'CRITICAL_SHORT',label: 'Crit. Short',   activeClass: 'text-red-400 border-red-600 bg-red-950/30'   },
  { key: 'SHORT_CREDIT',  label: 'Short',         activeClass: 'text-orange-400 border-orange-600 bg-orange-950/30' },
  { key: 'NEUTRAL',       label: 'Neutral',       activeClass: 'text-zinc-400 border-zinc-600 bg-zinc-950'   },
  { key: 'LONG_CREDIT',   label: 'Long',          activeClass: 'text-emerald-400 border-emerald-600 bg-emerald-950/30' },
];

const countFor = (results: MertonEventResult[], key: SignalFilter): number =>
  key === 'ALL' ? results.length : results.filter(r => r.signal === key).length;

export default function SignalSummaryBar({ results, filter, onFilter }: Props) {
  return (
    <div className="flex items-stretch border border-zinc-800 bg-black overflow-hidden">
      {TABS.map(({ key, label, activeClass }) => {
        const count    = countFor(results, key);
        const isActive = filter === key;
        return (
          <button
            key={key}
            onClick={() => onFilter(key)}
            className={`
              flex-1 flex items-center justify-center gap-2 px-3 py-2.5
              text-[10px] uppercase tracking-widest font-mono border-r border-zinc-900
              last:border-r-0 transition-all duration-150
              ${isActive
                ? `border-b-2 ${activeClass}`
                : 'text-zinc-600 border-b-2 border-b-transparent hover:text-zinc-300 hover:bg-zinc-950'
              }
            `}
          >
            <span>{label}</span>
            <span className={`text-[9px] ${isActive ? 'opacity-80' : 'text-zinc-800'}`}>
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
}