'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import {
  MertonEventResult,
  NewsItem,
  ScanSession,
  triggerManualScan,
  getStreamUrl,
} from '@/lib/api';
import ScannerHeader    from './ScannerHeader';
import SignalSummaryBar from './SignalSummaryBar';
import EventFeed        from './EventFeed';
import { ManualScanPanel } from './ManualScanPanel';

export type SignalFilter = 'ALL' | 'CRITICAL_SHORT' | 'SHORT_CREDIT' | 'NEUTRAL' | 'LONG_CREDIT';

// ── Aggregated news item carries its source ticker ─────────────────
interface AggregatedNewsItem extends NewsItem {
  ticker: string;
  signal: string;
}

// ── Signal → ticker badge color ────────────────────────────────────
const SIGNAL_BADGE: Record<string, string> = {
  CRITICAL_SHORT: 'bg-red-950 text-red-400 border-red-800',
  SHORT_CREDIT:   'bg-orange-950 text-orange-400 border-orange-800',
  NEUTRAL:        'bg-zinc-900 text-zinc-500 border-zinc-700',
  LONG_CREDIT:    'bg-emerald-950 text-emerald-400 border-emerald-800',
};

function formatNewsTime(isoTs: string): string {
  if (!isoTs) return '—';
  try {
    const d = new Date(isoTs + (isoTs.endsWith('Z') ? '' : 'Z'));
    const now = Date.now();
    const diffMin = Math.floor((now - d.getTime()) / 60_000);
    if (diffMin <  1)  return 'just now';
    if (diffMin < 60)  return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr  < 24)  return `${diffHr}h ago`;
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch {
    return '—';
  }
}

// ── Catalyst Wire component ────────────────────────────────────────
function CatalystWire({ items }: { items: AggregatedNewsItem[] }) {
  if (items.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center py-12">
        <p className="text-[10px] font-mono text-zinc-700 uppercase tracking-widest">
          No catalysts — awaiting scan
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto divide-y divide-zinc-900 scrollbar-none">
      {items.map((item, i) => (
        // FIX: Added the missing <a> tag that broke your compiler
        <a
          key={`${item.ticker}-${item.timestamp}-${i}`}
          href={item.url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="block px-4 py-4 hover:bg-zinc-950 transition-colors group"
        >
          {/* Top row: ticker badge + publisher + time */}
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`text-[9px] font-mono px-1.5 py-0.5 border uppercase tracking-wider shrink-0 ${SIGNAL_BADGE[item.signal] ?? SIGNAL_BADGE.NEUTRAL}`}
            >
              {item.ticker}
            </span>
            <span className="text-[9px] font-mono text-zinc-500 truncate flex-1 uppercase tracking-widest">
              {item.publisher}
            </span>
            <span className="text-[9px] font-mono text-zinc-600 shrink-0 tabular-nums">
              {formatNewsTime(item.timestamp)}
            </span>
          </div>

          {/* Headline */}
          <p className="text-[11px] font-mono text-zinc-300 leading-relaxed group-hover:text-white transition-colors line-clamp-2">
            {item.title}
          </p>
        </a>
      ))}
    </div>
  );
}

// ── Root terminal ──────────────────────────────────────────────────
export default function EventScannerTerminal() {
  const [session,    setSession]    = useState<ScanSession | null>(null);
  const [filter,     setFilter]     = useState<SignalFilter>('ALL');
  const [connected,  setConnected]  = useState(false);
  const [isScanning, setIsScanning] = useState(false);

  const esRef        = useRef<EventSource | null>(null);
  const scanTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── SSE connection ────────────────────────────────────────────
  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      const es = new EventSource(getStreamUrl());
      esRef.current = es;

      es.onopen = () => setConnected(true);

      es.onmessage = (event: MessageEvent) => {
        try {
          const data: ScanSession = JSON.parse(event.data);
          setSession(data);
          setIsScanning(false);
          if (scanTimerRef.current) clearTimeout(scanTimerRef.current);
        } catch {
          // keepalive or malformed — ignore
        }
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        reconnectTimer = setTimeout(connect, 10_000);
      };
    };

    connect();
    return () => {
      esRef.current?.close();
      clearTimeout(reconnectTimer);
      if (scanTimerRef.current) clearTimeout(scanTimerRef.current);
    };
  }, []);

// ── Manual scan handler ───────────────────────────────────────
  const handleManualScan = useCallback(async (tickers: string[]) => {
    if (isScanning) return;
    setIsScanning(true);

    try {
      await triggerManualScan(tickers);
      // ── UPGRADED: Matches the new 120s Axios threshold
      scanTimerRef.current = setTimeout(() => setIsScanning(false), 120_000);
    } catch (err: unknown) {
      console.error('Scan Error:', err);
      setIsScanning(false);
    }
  }, [isScanning]);

  // ── Aggregate + sort all news from scan results ──
  const allNews = useMemo((): AggregatedNewsItem[] => {
    if (!session?.results?.length) return [];

    const items: AggregatedNewsItem[] = session.results.flatMap(result =>
      (result.recent_news ?? []).map(n => ({
        ...n,
        ticker: result.ticker,
        signal: result.signal,
      }))
    );

    items.sort((a, b) => {
      if (!a.timestamp && !b.timestamp) return 0;
      if (!a.timestamp) return 1;
      if (!b.timestamp) return -1;
      return b.timestamp.localeCompare(a.timestamp);
    });

    return items;
  }, [session]);

  // ── Filtered feed rows ────────────────────────────────────────
  const filtered: MertonEventResult[] = useMemo(
    () => (session?.results ?? []).filter(r => filter === 'ALL' || r.signal === filter),
    [session, filter],
  );

  return (
    <div className="flex flex-col h-screen overflow-hidden font-mono bg-black text-white">
      {/* Top Header Row */}
      <ScannerHeader
        session={session}
        connected={connected}
        isScanning={isScanning}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left Panel: Data Feed ── */}
        <div className="flex-1 flex flex-col overflow-hidden border-r border-zinc-800 bg-black">
          <SignalSummaryBar
            results={session?.results ?? []}
            filter={filter}
            onFilter={setFilter}
          />
          <div className="flex-1 overflow-y-auto scrollbar-none">
            <EventFeed results={filtered} />
          </div>
        </div>

        {/* ── Right Panel: Controls & Catalyst Wire ── */}
        <div className="w-[380px] flex flex-col bg-black shrink-0">
          
          {/* FIX: Removed 'log' prop that crashed the panel */}
          <ManualScanPanel
            onScan={handleManualScan}
            isScanning={isScanning}
          />

          <div className="flex-1 flex flex-col overflow-hidden border-t border-zinc-800">
            {/* Wire Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-900 bg-zinc-950/50 shrink-0">
              <div className="flex items-center gap-2">
                {allNews.length > 0 && (
                  <span className="h-1.5 w-1.5 rounded-full bg-orange-500 animate-pulse shadow-[0_0_8px_rgba(249,115,22,0.8)]" />
                )}
                <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-400">
                  Live Catalyst Wire
                </span>
              </div>
              <span className="text-[9px] font-mono text-zinc-600 tabular-nums">
                {allNews.length} EVENT{allNews.length !== 1 ? 'S' : ''}
              </span>
            </div>

            {/* Scrolling Wire */}
            <CatalystWire items={allNews} />
          </div>

        </div>
      </div>
    </div>
  );
}