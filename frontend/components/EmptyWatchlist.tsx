'use client';

import { motion } from 'framer-motion';
import { Star, TrendingUp, Search } from 'lucide-react';
import Link from 'next/link';

export default function EmptyWatchlist() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="text-center py-20"
    >
      {/* Illustration using Lucide icons */}
      <div className="relative w-32 h-32 mx-auto mb-8">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0"
        >
          <div className="absolute top-0 left-1/2 -translate-x-1/2">
            <Star className="text-yellow-400" size={24} />
          </div>
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2">
            <Star className="text-yellow-400" size={20} />
          </div>
          <div className="absolute left-0 top-1/2 -translate-y-1/2">
            <Star className="text-yellow-400" size={16} />
          </div>
          <div className="absolute right-0 top-1/2 -translate-y-1/2">
            <Star className="text-yellow-400" size={16} />
          </div>
        </motion.div>

        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-20 h-20 bg-zinc-900 border-2 border-zinc-800 rounded-2xl flex items-center justify-center">
            <TrendingUp className="text-zinc-600" size={32} />
          </div>
        </div>
      </div>

      {/* Text */}
      <h3 className="text-2xl font-bold text-white mb-3">Your Watchlist is Empty</h3>
      <p className="text-zinc-400 mb-8 max-w-md mx-auto">
        Start tracking companies to monitor credit risk signals in real-time. 
        Add your first ticker using the search bar above.
      </p>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link href="/dashboard">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl text-white font-semibold hover:shadow-lg hover:shadow-emerald-500/50 transition-all flex items-center gap-2"
          >
            <TrendingUp size={20} />
            Discover Top Signals
          </motion.button>
        </Link>

        <Link href="/">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-4 bg-zinc-800 hover:bg-zinc-700 rounded-2xl text-white font-semibold transition-all flex items-center gap-2"
          >
            <Search size={20} />
            Search Companies
          </motion.button>
        </Link>
      </div>
    </motion.div>
  );
}