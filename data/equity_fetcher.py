"""
Equity data fetching using Yahoo Finance

Fetches:
- Market capitalization (E)
- Total debt (D)
- Equity volatility (sigma_E)
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    RISK_FREE_RATE,
    DEFAULT_TIME_HORIZON,
    HISTORICAL_VOL_WINDOW,
    MIN_VOLATILITY,
    MAX_VOLATILITY,
    MIN_MARKET_CAP,
    MIN_DEBT
)


class EquityDataFetcher:
    """
    Fetch equity data for Merton model inputs
    """
    
    def __init__(self, ticker, risk_free_rate=None, time_horizon=None):
        """
        Initialize fetcher
        
        Args:
            ticker (str): Stock ticker
            risk_free_rate (float): Override default r
            time_horizon (float): Override default T
        """
        self.ticker = ticker.upper()
        self.r = risk_free_rate or RISK_FREE_RATE
        self.T = time_horizon or DEFAULT_TIME_HORIZON
        
        self.stock = yf.Ticker(self.ticker)
        
        # Cache
        self._info = None
        self._balance_sheet = None
        self._history = None
    
    
    @property
    def info(self):
        """Lazy load company info"""
        if self._info is None:
            try:
                self._info = self.stock.info
            except Exception as e:
                warnings.warn(f"Failed to fetch info for {self.ticker}: {e}")
                self._info = {}
        return self._info
    
    
    @property
    def balance_sheet(self):
        """Lazy load balance sheet"""
        if self._balance_sheet is None:
            try:
                self._balance_sheet = self.stock.balance_sheet
            except Exception as e:
                warnings.warn(f"Failed to fetch balance sheet for {self.ticker}: {e}")
                self._balance_sheet = pd.DataFrame()
        return self._balance_sheet
    
    
    @property
    def history(self):
        """Lazy load price history"""
        if self._history is None:
            try:
                self._history = self.stock.history(period='3mo')
            except Exception as e:
                warnings.warn(f"Failed to fetch history for {self.ticker}: {e}")
                self._history = pd.DataFrame()
        return self._history
    
    
    def get_equity_value(self):
        """Get market capitalization (E)"""
        try:
            market_cap = self.info.get('marketCap')
            
            if market_cap and market_cap > MIN_MARKET_CAP:
                return float(market_cap)
            
            shares = self.info.get('sharesOutstanding')
            price = self.info.get('currentPrice')
            
            if shares and price:
                market_cap = shares * price
                if market_cap > MIN_MARKET_CAP:
                    return float(market_cap)
            
            if not self.history.empty:
                last_close = self.history['Close'].iloc[-1]
                if shares:
                    market_cap = shares * last_close
                    if market_cap > MIN_MARKET_CAP:
                        return float(market_cap)
            
            raise ValueError(f"Could not determine market cap for {self.ticker}")
        
        except Exception as e:
            raise ValueError(f"Error fetching equity value for {self.ticker}: {e}")
    
    
    def get_total_debt(self):
        """Get total debt (D)"""
        try:
            if self.balance_sheet.empty:
                raise ValueError("Balance sheet not available")
            
            debt_items = [
                'Total Debt',
                'Long Term Debt',
                'Short Long Term Debt',
                'Short Term Debt',
                'Current Debt'
            ]
            
            total_debt = 0
            
            for item in debt_items:
                if item in self.balance_sheet.index:
                    value = self.balance_sheet.loc[item].iloc[0]
                    
                    if pd.notna(value) and value > 0:
                        total_debt += value
            
            if total_debt < MIN_DEBT:
                warnings.warn(f"{self.ticker} has very low/no debt: ${total_debt:,.0f}")
                return max(total_debt, MIN_DEBT)
            
            return float(total_debt)
        
        except Exception as e:
            raise ValueError(f"Error fetching debt for {self.ticker}: {e}")
    
    
    def get_implied_volatility(self, days_to_expiry=30):
        """Get implied volatility from options"""
        try:
            expirations = self.stock.options
            
            if not expirations:
                return None
            
            target_date = datetime.now() + timedelta(days=days_to_expiry)
            expirations_dt = [datetime.strptime(exp, '%Y-%m-%d') for exp in expirations]
            
            closest_exp = min(expirations_dt, key=lambda x: abs((x - target_date).days))
            exp_str = closest_exp.strftime('%Y-%m-%d')
            
            opt_chain = self.stock.option_chain(exp_str)
            calls = opt_chain.calls
            
            if calls.empty:
                return None
            
            current_price = self.history['Close'].iloc[-1] if not self.history.empty else None
            
            if current_price is None:
                current_price = self.info.get('currentPrice', calls['strike'].median())
            
            calls['strike_diff'] = abs(calls['strike'] - current_price)
            atm_options = calls.nsmallest(3, 'strike_diff')
            
            impl_vols = atm_options['impliedVolatility'].dropna()
            
            if len(impl_vols) > 0:
                avg_iv = impl_vols.mean()
                
                if 0 < avg_iv < 5.0:
                    return float(max(MIN_VOLATILITY, min(MAX_VOLATILITY, avg_iv)))
            
            return None
        
        except Exception as e:
            warnings.warn(f"Could not fetch implied vol for {self.ticker}: {e}")
            return None
    
    
    def get_realized_volatility(self, window=None):
        """Calculate realized volatility"""
        try:
            if self.history.empty:
                raise ValueError("No price history available")
            
            window = window or HISTORICAL_VOL_WINDOW
            
            prices = self.history['Close']
            returns = np.log(prices / prices.shift(1)).dropna()
            
            if len(returns) < window:
                window = len(returns)
            
            daily_vol = returns.tail(window).std()
            annual_vol = daily_vol * np.sqrt(252)
            
            return float(max(MIN_VOLATILITY, min(MAX_VOLATILITY, annual_vol)))
        
        except Exception as e:
            raise ValueError(f"Error calculating realized vol for {self.ticker}: {e}")
    
    
    def get_equity_volatility(self):
        """Get volatility (implied first, fallback to realized)"""
        impl_vol = self.get_implied_volatility()
        if impl_vol is not None:
            return impl_vol
        
        return self.get_realized_volatility()
    
    
    def get_metadata(self):
        """Get company metadata"""
        return {
            'company_name': self.info.get('longName', self.info.get('shortName', self.ticker)),
            'sector': self.info.get('sector', 'Unknown'),
            'industry': self.info.get('industry', 'Unknown')
        }
    
    
    def fetch(self):
        """
        Fetch all Merton inputs
        
        Returns:
            dict: All required inputs
        """
        try:
            E = self.get_equity_value()
            D = self.get_total_debt()
            
            impl_vol = self.get_implied_volatility()
            if impl_vol is not None:
                sigma_E = impl_vol
                vol_source = 'implied'
            else:
                sigma_E = self.get_realized_volatility()
                vol_source = 'realized'
            
            metadata = self.get_metadata()
            
            return {
                'ticker': self.ticker,
                'company_name': metadata['company_name'],
                'sector': metadata['sector'],
                'industry': metadata['industry'],
                'E': E,
                'D': D,
                'sigma_E': sigma_E,
                'r': self.r,
                'T': self.T,
                'data_quality': {
                    'volatility_source': vol_source,
                    'has_options': impl_vol is not None,
                    'leverage': D / (E + D)
                }
            }
        
        except Exception as e:
            raise ValueError(f"Failed to fetch inputs for {self.ticker}: {e}")


def fetch_batch(tickers, max_failures=0.3):
    """
    Fetch data for multiple tickers
    
    Args:
        tickers (list): List of tickers
        max_failures (float): Max failure rate allowed
    
    Returns:
        list: Successful results
    """
    results = []
    failures = []
    
    for ticker in tickers:
        try:
            fetcher = EquityDataFetcher(ticker)
            data = fetcher.fetch()
            results.append(data)
            print(f"✓ {ticker}")
        
        except Exception as e:
            failures.append(ticker)
            print(f"✗ {ticker}: {e}")
    
    if len(failures) / len(tickers) > max_failures:
        warnings.warn(f"High failure rate: {len(failures)}/{len(tickers)}")
    
    return results