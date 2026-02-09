'use client';

export default function SkeletonLoader() {
  return (
    <div className="w-full max-w-6xl mx-auto animate-pulse">
      {/* Company Header - matches actual header height */}
      <div className="text-center mb-8">
        <div className="h-10 bg-zinc-800 rounded-lg w-2/3 mx-auto mb-3"></div>
        <div className="h-5 bg-zinc-800 rounded w-1/3 mx-auto"></div>
      </div>
      
      {/* Stats Grid - EXACT dimensions to match SignalCard */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div 
            key={i} 
            className="bg-zinc-900 rounded-2xl p-6 border border-zinc-800"
            style={{ minHeight: '108px' }} // Exact height of actual stat cards
          >
            <div className="h-4 bg-zinc-800 rounded w-2/3 mb-4"></div>
            <div className="h-8 bg-zinc-800 rounded w-4/5"></div>
          </div>
        ))}
      </div>
      
      {/* Merton Results - matches MertonResultsCard */}
      <div 
        className="bg-zinc-900 rounded-3xl p-8 border border-zinc-800 mb-8"
        style={{ minHeight: '380px' }} // Prevents jump
      >
        <div className="h-7 bg-zinc-800 rounded w-1/3 mb-6"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4, 5].map((i) => (
            <div 
              key={i} 
              className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700/50"
              style={{ minHeight: '92px' }} // Exact metric card height
            >
              <div className="h-3 bg-zinc-700 rounded w-1/2 mb-3"></div>
              <div className="h-9 bg-zinc-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Signal Card - matches SignalCard dimensions */}
      <div 
        className="bg-gradient-to-br from-zinc-700/20 to-zinc-600/20 border-2 border-zinc-600/50 rounded-3xl p-8 mb-8"
        style={{ minHeight: '220px' }} // Prevents layout shift
      >
        <div className="flex items-center justify-between mb-6">
          <div className="h-8 bg-zinc-800 rounded w-1/3"></div>
          <div className="h-10 bg-zinc-800 rounded-full w-10"></div>
        </div>
        <div className="grid grid-cols-3 gap-6 mb-6">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <div className="h-3 bg-zinc-800 rounded w-2/3 mb-2"></div>
              <div className="h-7 bg-zinc-800 rounded w-4/5"></div>
            </div>
          ))}
        </div>
        <div className="h-4 bg-zinc-800 rounded w-full"></div>
      </div>

      {/* Sensitivity Toggle Button */}
      <div className="flex justify-center mb-8">
        <div className="h-14 bg-purple-500/20 border border-purple-500/50 rounded-2xl w-64"></div>
      </div>
    </div>
  );
}