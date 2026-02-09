'use client';

import { useState, useEffect } from 'react';

export interface WatchlistItem {
  ticker: string;
  addedAt: string;
  lastChecked?: string;
}

export const useWatchlist = () => {
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('watchlist');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setWatchlist(Array.isArray(parsed) ? parsed : []);
      } catch (e) {
        console.error('Failed to parse watchlist:', e);
        setWatchlist([]);
      }
    }
    setIsLoading(false);
  }, []);

  // Save to localStorage whenever watchlist changes
  useEffect(() => {
    if (!isLoading) {
      localStorage.setItem('watchlist', JSON.stringify(watchlist));
    }
  }, [watchlist, isLoading]);

  const addTicker = (ticker: string) => {
    const upperTicker = ticker.trim().toUpperCase();
    if (upperTicker && !watchlist.includes(upperTicker)) {
      setWatchlist((prev) => [...prev, upperTicker]);
      return true;
    }
    return false;
  };

  const removeTicker = (ticker: string) => {
    setWatchlist((prev) => prev.filter((t) => t !== ticker));
  };

  const clearWatchlist = () => {
    setWatchlist([]);
  };

  const isWatched = (ticker: string) => {
    return watchlist.includes(ticker.toUpperCase());
  };

  return {
    watchlist,
    isLoading,
    addTicker,
    removeTicker,
    clearWatchlist,
    isWatched,
  };
};