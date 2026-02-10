'use client';

export default function SkeletonLoader() {
  return (
    <div className="w-full max-w-6xl mx-auto animate-pulse">
      {/* Header */}
      <div className="text-center border-b border-zinc-900 pb-8 mb-12">
        <div className="h-10 bg-zinc-900 w-2/3 mx-auto mb-3 border border-zinc-800"></div>
        <div className="h-4 bg-zinc-900 w-1/3 mx-auto border border-zinc-800"></div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 border-t border-l border-zinc-800 mb-12">
        {[1, 2, 3, 4].map((i) => (
          <div 
            key={i} 
            className="bg-black p-8 border-r border-b border-zinc-800"
          >
            <div className="h-3 bg-zinc-900 w-2/3 mb-4 border border-zinc-800"></div>
            <div className="h-8 bg-zinc-900 w-4/5 border border-zinc-800"></div>
          </div>
        ))}
      </div>
      
      {/* Merton Results */}
      <div className="border border-zinc-800 bg-black mb-12">
        <div className="h-16 bg-zinc-950 border-b border-zinc-800"></div>
        <div className="grid md:grid-cols-2 border-zinc-800">
          {[1, 2, 3, 4].map((i) => (
            <div 
              key={i} 
              className="p-8 border-r border-b border-zinc-800"
            >
              <div className="h-3 bg-zinc-900 w-1/2 mb-3 border border-zinc-800"></div>
              <div className="h-9 bg-zinc-900 w-3/4 border border-zinc-800"></div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Signal Card */}
      <div className="border-2 border-zinc-800 bg-black">
        <div className="h-24 bg-zinc-950 border-b border-zinc-800"></div>
        <div className="h-32 bg-black"></div>
      </div>
    </div>
  );
}