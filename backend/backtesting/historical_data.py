"""
Fetch historical equity data for backtesting
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings


class HistoricalDataFetcher:
    """
    Fetch historical equity data for backtesting
    
    Uses yfinance to get historical prices, calculate realized volatility,
    and retrieve balance sheet data from past periods
    """
    
    def __init__(self, ticker):
        """
        Initialize fetcher for a specific ticker
        
        Args:
            ticker (str): Stock ticker symbol
        """
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(self.ticker)
    
    
    def get_historical_snapshot(self, date, lookback_days=60):
        """
        Get equity data snapshot as of a specific historical date
        
        Args:
            date (str or datetime): Target date for snapshot (YYYY-MM-DD)
            lookback_days (int): Days to look back for volatility calculation
        
        Returns:
            dict: {E, D, sigma_E, date, price, shares}
        """
        if isinstance(date, str):
            target_date = pd.to_datetime(date)
        else:
            target_date = date
        
        # Get historical prices
        start_date = target_date - timedelta(days=lookback_days + 30)  # Extra buffer
        end_date = target_date + timedelta(days=1)  # Include target date
        
        try:
            hist = self.stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No price data available for {self.ticker} around {target_date}")
            
            # Get price on target date (or closest available)
            if target_date in hist.index:
                target_price = hist.loc[target_date, 'Close']
            else:
                # Find closest date
                closest_date = hist.index[hist.index <= target_date].max()
                if pd.isna(closest_date):
                    raise ValueError(f"No price data before {target_date}")
                target_price = hist.loc[closest_date, 'Close']
                target_date = closest_date
            
            # Calculate realized volatility using data up to target date
            prices_up_to_date = hist[hist.index <= target_date]
            
            if len(prices_up_to_date) < 30:
                raise ValueError(f"Insufficient price history (only {len(prices_up_to_date)} days)")
            
            # Use last 60 days (or less if not available)
            vol_window = min(lookback_days, len(prices_up_to_date) - 1)
            recent_prices = prices_up_to_date.tail(vol_window + 1)
            
            # Calculate log returns
            log_returns = np.log(recent_prices['Close'] / recent_prices['Close'].shift(1))
            sigma_E = log_returns.std() * np.sqrt(252)  # Annualize
            
            # Get shares outstanding
            shares = self._get_shares_outstanding(target_date)
            
            # Calculate market cap
            E = target_price * shares
            
            # Get total debt (use most recent balance sheet before target date)
            D = self._get_total_debt(target_date)
            
            return {
                'ticker': self.ticker,
                'date': target_date.strftime('%Y-%m-%d'),
                'price': target_price,
                'shares_outstanding': shares,
                'E': E,
                'D': D,
                'sigma_E': sigma_E,
                'volatility_window_days': vol_window,
            }
        
        except Exception as e:
            raise ValueError(f"Failed to get snapshot for {self.ticker} on {date}: {e}")
    
    
    def get_time_series(self, start_date, end_date, frequency='weekly'):
        """
        Get time series of equity snapshots
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            frequency (str): 'daily', 'weekly', or 'monthly'
        
        Returns:
            pd.DataFrame: Time series of snapshots
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Generate date range
        if frequency == 'daily':
            dates = pd.date_range(start, end, freq='D')
        elif frequency == 'weekly':
            dates = pd.date_range(start, end, freq='W')
        elif frequency == 'monthly':
            dates = pd.date_range(start, end, freq='MS')
        else:
            raise ValueError(f"Invalid frequency: {frequency}")
        
        # Get snapshot for each date
        results = []
        
        for date in dates:
            try:
                snapshot = self.get_historical_snapshot(date)
                results.append(snapshot)
            except Exception as e:
                warnings.warn(f"Failed to get snapshot for {date}: {e}")
                continue
        
        if not results:
            raise ValueError(f"No snapshots retrieved for {self.ticker}")
        
        return pd.DataFrame(results)
    
    
    def _get_shares_outstanding(self, date):
        """
        Get shares outstanding as of a date
        
        Uses info dict from yfinance (current data only)
        For historical accuracy, this is a limitation - uses current shares
        
        Args:
            date (datetime): Target date
        
        Returns:
            float: Shares outstanding
        """
        try:
            info = self.stock.info
            
            # Try multiple fields
            shares = (
                info.get('sharesOutstanding') or
                info.get('impliedSharesOutstanding') or
                info.get('floatShares')
            )
            
            if shares and shares > 0:
                return float(shares)
            
            # Fallback: calculate from market cap and price
            if 'marketCap' in info and 'currentPrice' in info:
                return info['marketCap'] / info['currentPrice']
            
            raise ValueError("No shares outstanding data available")
        
        except Exception as e:
            raise ValueError(f"Failed to get shares outstanding: {e}")
    
    
    def _get_total_debt(self, date):
        """
        Get total debt as of a date
        
        Uses balance sheet data (quarterly)
        
        Args:
            date (datetime): Target date
        
        Returns:
            float: Total debt
        """
        try:
            # Get quarterly balance sheet
            balance_sheet = self.stock.quarterly_balance_sheet
            
            if balance_sheet.empty:
                raise ValueError("No balance sheet data available")
            
            # Find most recent balance sheet before target date
            available_dates = balance_sheet.columns
            past_dates = [d for d in available_dates if d <= date]
            
            if not past_dates:
                # Use oldest available
                relevant_date = available_dates[-1]
                warnings.warn(
                    f"No balance sheet before {date}, using oldest: {relevant_date}"
                )
            else:
                relevant_date = max(past_dates)
            
            bs = balance_sheet[relevant_date]
            
            # Aggregate debt items
            debt_items = [
                'Total Debt',
                'Long Term Debt',
                'Short Long Term Debt',
                'Short Term Debt',
                'Current Debt',
                'Long Term Debt And Capital Lease Obligation',
            ]
            
            total_debt = 0
            for item in debt_items:
                if item in bs.index and not pd.isna(bs[item]):
                    total_debt += abs(float(bs[item]))
            
            if total_debt == 0:
                raise ValueError("Total debt is zero or unavailable")
            
            return total_debt
        
        except Exception as e:
            raise ValueError(f"Failed to get total debt: {e}")


# ========== CONVENIENCE FUNCTIONS ==========

def get_historical_snapshot(ticker, date, lookback_days=60):
    """
    Convenience function to get historical snapshot
    
    Args:
        ticker (str): Stock ticker
        date (str): Target date (YYYY-MM-DD)
        lookback_days (int): Volatility lookback window
    
    Returns:
        dict: Historical snapshot
    """
    fetcher = HistoricalDataFetcher(ticker)
    return fetcher.get_historical_snapshot(date, lookback_days)


def get_time_series(ticker, start_date, end_date, frequency='weekly'):
    """
    Convenience function to get time series
    
    Args:
        ticker (str): Stock ticker
        start_date (str): Start date
        end_date (str): End date
        frequency (str): Sampling frequency
    
    Returns:
        pd.DataFrame: Time series
    """
    fetcher = HistoricalDataFetcher(ticker)
    return fetcher.get_time_series(start_date, end_date, frequency)