"""
Market credit spread fetcher using FRED indices

Since individual corporate bond data requires expensive subscriptions,
we use sector-wide credit spreads by rating tier as proxies.

Data source: Federal Reserve Economic Data (FRED)
Indices: ICE BofA Option-Adjusted Spreads (OAS)
"""
from fredapi import Fred
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FRED_API_KEY, FRED_SPREAD_SERIES


class MarketSpreadFetcher:
    """
    Fetch market credit spreads from FRED API
    
    Uses rating-based proxies when individual bond data unavailable
    """
    
    def __init__(self, api_key=None):
        """
        Initialize FRED connection
        
        Args:
            api_key (str): FRED API key (defaults to config)
        """
        self.api_key = api_key or FRED_API_KEY
        
        if not self.api_key:
            raise ValueError(
                "FRED API key required. Get one free at: "
                "https://fred.stlouisfed.org/docs/api/api_key.html"
            )
        
        self.fred = Fred(api_key=self.api_key)
        self._spread_cache = {}
        self._cache_timestamp = None
    
    
    def get_current_spreads(self, force_refresh=False):
        """
        Fetch latest OAS for all rating categories
        
        Args:
            force_refresh (bool): Bypass cache
        
        Returns:
            dict: {rating: spread_bps}
        """
        # Check cache (valid for 1 hour)
        if not force_refresh and self._spread_cache:
            if self._cache_timestamp:
                age = datetime.now() - self._cache_timestamp
                if age.total_seconds() < 3600:  # 1 hour
                    return self._spread_cache
        
        spreads = {}
        
        for rating, series_id in FRED_SPREAD_SERIES.items():
            try:
                # Fetch last 5 days (in case of holidays/weekends)
                data = self.fred.get_series(
                    series_id,
                    observation_start=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
                )
                
                if not data.empty:
                    spreads[rating] = float(data.iloc[-1] * 100)  # Convert % to bps
                else:
                    spreads[rating] = None
            
            except Exception as e:
                warnings.warn(f"Failed to fetch {rating} spread ({series_id}): {e}")
                spreads[rating] = None
        
        # Update cache
        self._spread_cache = spreads
        self._cache_timestamp = datetime.now()
        
        return spreads
    
    
    def get_spread_by_rating(self, rating):
        """
        Get spread for a specific rating
        
        Args:
            rating (str): Credit rating (e.g., 'BBB', 'B')
        
        Returns:
            float: Spread in basis points
        """
        rating = self._normalize_rating(rating)
        spreads = self.get_current_spreads()
        
        spread = spreads.get(rating)
        
        if spread is None:
            # Fallback to BBB if rating unavailable
            spread = spreads.get('BBB', 200)
            warnings.warn(f"Rating {rating} spread unavailable, using BBB: {spread} bps")
        
        return spread
    
    
    def estimate_rating_from_fundamentals(self, ticker_data):
        """
        Estimate credit rating from financial metrics
        
        Uses leverage and interest coverage heuristics when
        actual rating is unavailable
        
        Args:
            ticker_data (dict): Must contain 'E' and 'D'
        
        Returns:
            str: Estimated rating
        """
        try:
            E = ticker_data['E']
            D = ticker_data['D']
            
            # Calculate leverage ratio
            leverage = D / (E + D)
            
            # Rating heuristics (simplified Moody's/S&P methodology)
            if leverage < 0.20:
                return 'AA'   # Very low leverage
            elif leverage < 0.35:
                return 'A'    # Low leverage
            elif leverage < 0.50:
                return 'BBB'  # Moderate leverage (investment grade floor)
            elif leverage < 0.65:
                return 'BB'   # High leverage (high yield ceiling)
            elif leverage < 0.80:
                return 'B'    # Very high leverage
            else:
                return 'CCC'  # Distressed
        
        except Exception as e:
            warnings.warn(f"Could not estimate rating: {e}")
            return 'BBB'  # Conservative default
    
    
    def get_company_rating(self, ticker, ticker_data=None):
        """
        Get or estimate credit rating for a company
        
        Priority:
        1. Try to fetch actual rating from yfinance (if available)
        2. Estimate from financial metrics
        
        Args:
            ticker (str): Stock ticker
            ticker_data (dict): Optional pre-fetched data with E, D
        
        Returns:
            str: Credit rating
        """
        # Method 1: Try yfinance (rarely available)
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if 'creditRating' in info and info['creditRating']:
                return self._normalize_rating(info['creditRating'])
        
        except Exception:
            pass
        
        # Method 2: Estimate from fundamentals
        if ticker_data:
            return self.estimate_rating_from_fundamentals(ticker_data)
        
        # Fallback
        return 'BBB'
    
    
    def get_market_spread(self, ticker, ticker_data=None):
        """
        Get market credit spread for a company
        
        This is the main interface method
        
        Args:
            ticker (str): Stock ticker
            ticker_data (dict): Optional pre-fetched equity data
        
        Returns:
            float: Market spread in basis points
        """
        # Get rating
        rating = self.get_company_rating(ticker, ticker_data)
        
        # Get spread for that rating
        spread = self.get_spread_by_rating(rating)
        
        return spread
    
    
    def _normalize_rating(self, rating):
        """
        Normalize rating to standard buckets
        
        Converts variants like 'BBB+', 'Baa2', etc. to base rating
        
        Args:
            rating (str): Raw rating
        
        Returns:
            str: Normalized rating
        """
        if not rating:
            return 'BBB'
        
        rating = str(rating).upper().strip()
        
        # Remove modifiers (+, -, 1, 2, 3)
        rating = rating.replace('+', '').replace('-', '')
        rating = ''.join([c for c in rating if c.isalpha()])
        
        # Map Moody's to S&P equivalents
        moody_map = {
            'AAA': 'AAA',
            'AA': 'AA',
            'A': 'A',
            'BAA': 'BBB',  # Moody's Baa = S&P BBB
            'BA': 'BB',
            'B': 'B',
            'CAA': 'CCC',
            'CA': 'CCC',
            'C': 'CCC'
        }
        
        # Check if it's a Moody's rating
        for moody, sp in moody_map.items():
            if rating.startswith(moody):
                return sp
        
        # Standard S&P ratings
        if rating.startswith('AAA'):
            return 'AAA'
        elif rating.startswith('AA'):
            return 'AA'
        elif rating.startswith('A'):
            return 'A'
        elif rating.startswith('BBB'):
            return 'BBB'
        elif rating.startswith('BB'):
            return 'BB'
        elif rating.startswith('B'):
            return 'B'
        elif rating.startswith('CCC') or rating.startswith('CC') or rating.startswith('C'):
            return 'CCC'
        
        # Default to investment grade floor
        return 'BBB'
    
    
    def get_spread_timeseries(self, rating, start_date=None, end_date=None):
        """
        Get historical spread data for backtesting
        
        Args:
            rating (str): Credit rating
            start_date (str): Start date 'YYYY-MM-DD'
            end_date (str): End date 'YYYY-MM-DD'
        
        Returns:
            pd.Series: Historical spreads
        """
        rating = self._normalize_rating(rating)
        series_id = FRED_SPREAD_SERIES.get(rating)
        
        if not series_id:
            raise ValueError(f"No FRED series for rating: {rating}")
        
        try:
            data = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )
            return data
        
        except Exception as e:
            raise ValueError(f"Failed to fetch timeseries for {rating}: {e}")
    
    
    def get_all_spreads_summary(self):
        """
        Get summary table of all current spreads
        
        Returns:
            pd.DataFrame: Summary table
        """
        spreads = self.get_current_spreads()
        
        df = pd.DataFrame([
            {
                'Rating': rating,
                'Spread (bps)': spread,
                'Spread (%)': spread / 100 if spread else None,
                'Category': 'Investment Grade' if rating in ['AAA', 'AA', 'A', 'BBB'] else 'High Yield'
            }
            for rating, spread in spreads.items()
            if rating not in ['IG_MASTER', 'HY_MASTER']  # Exclude master indices
        ])
        
        return df.sort_values('Spread (bps)')


# ========== CONVENIENCE FUNCTIONS ==========

def get_market_spread(ticker, ticker_data=None, api_key=None):
    """
    Convenience function to get market spread
    
    Args:
        ticker (str): Stock ticker
        ticker_data (dict): Optional equity data
        api_key (str): Optional FRED API key
    
    Returns:
        float: Market spread in bps
    """
    fetcher = MarketSpreadFetcher(api_key=api_key)
    return fetcher.get_market_spread(ticker, ticker_data)


def get_spread_table(api_key=None):
    """
    Get summary table of all current spreads
    
    Args:
        api_key (str): Optional FRED API key
    
    Returns:
        pd.DataFrame: Spread summary
    """
    fetcher = MarketSpreadFetcher(api_key=api_key)
    return fetcher.get_all_spreads_summary()