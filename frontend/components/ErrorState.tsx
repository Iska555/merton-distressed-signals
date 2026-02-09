'use client';

import { motion } from 'framer-motion';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  error: string;
  onRetry?: () => void;
  ticker?: string;
}

export default function ErrorState({ error, onRetry, ticker }: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="max-w-2xl mx-auto bg-gradient-to-br from-red-500/10 to-orange-500/10 border-2 border-red-500/50 rounded-3xl p-8 mb-8 backdrop-blur-sm"
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center">
            <AlertCircle className="text-red-400" size={24} />
          </div>
        </div>
        
        <div className="flex-1">
          <h3 className="text-xl font-bold text-red-400 mb-2">
            Analysis Failed
            {ticker && ` for ${ticker}`}
          </h3>
          
          <p className="text-zinc-300 mb-4">
            {error}
          </p>
          
          {/* Common error hints */}
          <div className="text-sm text-zinc-400 mb-4 space-y-1">
            <p>Common issues:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Invalid ticker symbol</li>
              <li>Company has insufficient financial data</li>
              <li>API rate limit exceeded</li>
              <li>Network connectivity issues</li>
            </ul>
          </div>
          
          {onRetry && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onRetry}
              className="flex items-center gap-2 px-6 py-3 bg-red-500 hover:bg-red-600 rounded-xl text-white font-semibold transition-colors"
            >
              <RefreshCw size={18} />
              Try Again
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );
}