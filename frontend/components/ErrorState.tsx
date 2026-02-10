'use client';

import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  error: string;
  onRetry?: () => void;
  ticker?: string;
}

export default function ErrorState({ error, onRetry, ticker }: ErrorStateProps) {
  return (
    <div className="max-w-2xl mx-auto border-2 border-red-900/30 bg-black mb-12">
      <div className="p-8 flex items-start gap-6">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 border border-red-900/50 flex items-center justify-center">
            <AlertCircle className="text-red-500" size={24} />
          </div>
        </div>
        
        <div className="flex-1">
          <h3 className="text-xl font-serif text-red-500 mb-3 uppercase tracking-wide">
            Analysis Failed
            {ticker && ` • ${ticker}`}
          </h3>
          
          <p className="text-zinc-400 mb-6 text-sm font-mono leading-relaxed">
            {error}
          </p>
          
          <div className="text-[10px] text-zinc-600 mb-6 space-y-2 font-mono uppercase tracking-wider">
            <p>Common Issues:</p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Invalid ticker symbol</li>
              <li>Insufficient financial data</li>
              <li>API rate limit exceeded</li>
              <li>Network connectivity</li>
            </ul>
          </div>
          
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-3 px-6 py-3 bg-red-900/20 border border-red-900/50 text-red-500 text-[11px] font-bold uppercase tracking-[0.25em] hover:bg-red-900/30 transition-colors"
            >
              <RefreshCw size={14} />
              Retry Analysis
            </button>
          )}
        </div>
      </div>
    </div>
  );
}