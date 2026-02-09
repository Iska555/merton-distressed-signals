'use client';

export default function SkeletonLoader() {
  return (
    <div className="w-full max-w-4xl mx-auto animate-pulse">
      {/* Header */}
      <div className="h-8 bg-zinc-800 rounded-lg w-1/3 mb-8"></div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-zinc-900 rounded-2xl p-6 border border-zinc-800">
            <div className="h-4 bg-zinc-800 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-zinc-800 rounded w-3/4"></div>
          </div>
        ))}
      </div>
      
      {/* Merton Results */}
      <div className="bg-zinc-900 rounded-2xl p-8 border border-zinc-800 mb-8">
        <div className="h-6 bg-zinc-800 rounded w-1/4 mb-6"></div>
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex justify-between">
              <div className="h-4 bg-zinc-800 rounded w-1/3"></div>
              <div className="h-4 bg-zinc-800 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Signal */}
      <div className="bg-zinc-900 rounded-2xl p-8 border border-zinc-800">
        <div className="h-12 bg-zinc-800 rounded w-2/3 mx-auto"></div>
      </div>
    </div>
  );
}