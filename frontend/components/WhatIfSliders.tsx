'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sliders } from 'lucide-react';

interface WhatIfSlidersProps {
  baseE: number;
  baseD: number;
  baseSigmaE: number;
  onParametersChange: (params: { E: number; D: number; sigma_E: number }) => void;
}

export default function WhatIfSliders({
  baseE,
  baseD,
  baseSigmaE,
  onParametersChange,
}: WhatIfSlidersProps) {
  const [volShock, setVolShock] = useState(0);
  const [debtShock, setDebtShock] = useState(0);

  useEffect(() => {
    const newE = baseE;
    const newD = baseD * (1 + debtShock / 100);
    const newSigmaE = baseSigmaE * (1 + volShock / 100);

    onParametersChange({ E: newE, D: newD, sigma_E: newSigmaE });
  }, [volShock, debtShock]);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-zinc-900 rounded-3xl p-6 border border-zinc-800"
    >
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <Sliders className="text-purple-400" size={20} />
        What-If Analysis
      </h3>

      <div className="space-y-6">
        {/* Volatility Slider */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm text-zinc-400">Equity Volatility Shock</label>
            <span className="text-sm font-medium text-white">
              {volShock > 0 ? '+' : ''}
              {volShock}%
            </span>
          </div>
          <input
            type="range"
            min="-50"
            max="50"
            step="5"
            value={volShock}
            onChange={(e) => setVolShock(Number(e.target.value))}
            className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <div className="flex justify-between text-xs text-zinc-500 mt-1">
            <span>-50%</span>
            <span>0%</span>
            <span>+50%</span>
          </div>
        </div>

        {/* Debt Slider */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm text-zinc-400">Total Debt Shock</label>
            <span className="text-sm font-medium text-white">
              {debtShock > 0 ? '+' : ''}
              {debtShock}%
            </span>
          </div>
          <input
            type="range"
            min="-50"
            max="50"
            step="5"
            value={debtShock}
            onChange={(e) => setDebtShock(Number(e.target.value))}
            className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-red-500"
          />
          <div className="flex justify-between text-xs text-zinc-500 mt-1">
            <span>-50%</span>
            <span>0%</span>
            <span>+50%</span>
          </div>
        </div>

        {/* Reset Button */}
        <button
          onClick={() => {
            setVolShock(0);
            setDebtShock(0);
          }}
          className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-sm text-zinc-400 transition-colors"
        >
          Reset to Base Case
        </button>
      </div>
    </motion.div>
  );
}