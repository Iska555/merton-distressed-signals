'use client';

import { Activity, Wifi, WifiOff, Loader2 } from 'lucide-react';
import { ScanSession } from '@/lib/api';

interface Props {
  session:    ScanSession | null;
  connected:  boolean;
  isScanning: boolean;
}

export default function ScannerHeader({ session, connected, isScanning }: Props) {
  const lastUpdated = session
    ? new Date(session.triggered_at + (session.triggered_at.endsWith('Z') ? '' : 'Z'))
        .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : null;

  return (
    <div className="border border-zinc-800 bg-black px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">

      {/* Title */}
      <div className="flex items-center gap-4">
        <div className="p-2 border border-zinc-800">
          <Activity size={16} className="text-zinc-400" />
        </div>
        <div>
          <h1 className="text-xs font-mono uppercase tracking-[0.25em] text-white">
            Merton Event Scanner
          </h1>
          <p className="text-[10px] text-zinc-600 uppercase tracking-widest mt-0.5">
            Equity vol shock detection · Structural credit lag · Alpha gap signals
          </p>
        </div>
      </div>

      {/* Status cluster */}
      <div className="flex flex-wrap items-center gap-5 text-[10px] font-mono uppercase tracking-widest">

        {/* Connection */}
        <div className="flex items-center gap-1.5">
          {connected
            ? <Wifi size={11} className="text-emerald-500" />
            : <WifiOff size={11} className="text-zinc-600" />}
          <span className={connected ? 'text-emerald-500' : 'text-zinc-600'}>
            {connected ? 'Live' : 'Reconnecting'}
          </span>
        </div>

        {/* Scanning pulse */}
        {isScanning && (
          <div className="flex items-center gap-1.5 text-amber-400">
            <Loader2 size={11} className="animate-spin" />
            <span>Scanning</span>
          </div>
        )}

        {/* Session stats */}
        {session ? (
          <>
            <div className="text-zinc-500">
              <span className="text-white">{session.signals_fired}</span>
              {' '}Signal{session.signals_fired !== 1 ? 's' : ''}
            </div>
            <div className="text-zinc-500">
              <span className="text-white">{session.total_screened}</span>
              {' '}Screened
            </div>
            <div className="text-zinc-600">
              Updated <span className="text-zinc-400">{lastUpdated}</span>
            </div>
            <div className="text-zinc-700 hidden sm:block">
              {session.session_id}
            </div>
          </>
        ) : (
          <span className="text-zinc-700">Awaiting first scan</span>
        )}
      </div>
    </div>
  );
}