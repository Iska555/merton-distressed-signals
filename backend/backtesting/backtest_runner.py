"""
Backtest runner for Merton model validation
"""
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import (
    solve_merton_system,
    merton_distance_to_default,
    merton_default_probability,
    merton_credit_spread
)
from backtesting.historical_data import HistoricalDataFetcher
from config import SIGNAL_THRESHOLD_STRONG, SIGNAL_THRESHOLD_MODERATE


class BacktestRunner:
    """
    Run historical backtests of Merton model signals
    
    Validates model performance on known credit events
    """
    
    def __init__(self, ticker, r=0.0352, T=1.0):
        """
        Initialize backtest runner
        
        Args:
            ticker (str): Stock ticker to backtest
            r (float): Risk-free rate
            T (float): Time horizon (years)
        """
        self.ticker = ticker.upper()
        self.r = r
        self.T = T
        self.fetcher = HistoricalDataFetcher(ticker)
    
    
    def run_backtest(self, start_date, end_date, frequency='weekly'):
        """
        Run full backtest over a time period
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            frequency (str): Sampling frequency
        
        Returns:
            pd.DataFrame: Backtest results with signals
        """
        print(f"\n{'='*60}")
        print(f"RUNNING BACKTEST: {self.ticker}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Frequency: {frequency}")
        print(f"{'='*60}\n")
        
        # Get historical time series
        try:
            time_series = self.fetcher.get_time_series(start_date, end_date, frequency)
        except Exception as e:
            raise ValueError(f"Failed to fetch time series: {e}")
        
        print(f"✓ Fetched {len(time_series)} historical snapshots\n")
        
        # Run Merton model on each snapshot
        results = []
        
        for idx, row in time_series.iterrows():
            try:
                # Run Merton model
                V, sigma_V, method = solve_merton_system(
                    E=row['E'],
                    sigma_E=row['sigma_E'],
                    D=row['D'],
                    r=self.r,
                    T=self.T
                )
                
                # Calculate metrics
                dd = merton_distance_to_default(V, sigma_V, row['D'], self.r, self.T)
                pd_val = merton_default_probability(V, sigma_V, row['D'], self.r, self.T)
                spread = merton_credit_spread(V, sigma_V, row['D'], self.r, self.T)
                
                # Classify signal
                signal = self._classify_signal(dd, spread)
                signal_strength = self._calculate_signal_strength(dd)
                
                results.append({
                    'date': row['date'],
                    'price': row['price'],
                    'E': row['E'],
                    'D': row['D'],
                    'sigma_E': row['sigma_E'],
                    'V': V,
                    'sigma_V': sigma_V,
                    'leverage': row['D'] / V,
                    'distance_to_default': dd,
                    'default_probability': pd_val,
                    'theo_spread_bps': spread,
                    'signal': signal,
                    'signal_strength': signal_strength,
                    'solver_method': method,
                })
                
                print(f"  {row['date']}: DD = {dd:.2f}σ, Spread = {spread:.0f} bps, Signal = {signal}")
            
            except Exception as e:
                warnings.warn(f"Failed to process {row['date']}: {e}")
                continue
        
        if not results:
            raise ValueError("No successful backtest results")
        
        df = pd.DataFrame(results)
        
        print(f"\n{'='*60}")
        print(f"✓ BACKTEST COMPLETE: {len(results)}/{len(time_series)} periods successful")
        print(f"{'='*60}\n")
        
        return df
    
    
    def identify_warnings(self, backtest_results, dd_threshold=2.0):
        """
        Identify when model would have issued warnings
        
        Args:
            backtest_results (pd.DataFrame): Results from run_backtest
            dd_threshold (float): Distance to default threshold for warning
        
        Returns:
            pd.DataFrame: Warning events
        """
        warnings_df = backtest_results[
            backtest_results['distance_to_default'] < dd_threshold
        ].copy()
        
        # Add days until threshold crossed
        warnings_df['days_since_start'] = pd.to_datetime(warnings_df['date']) - pd.to_datetime(backtest_results.iloc[0]['date'])
        warnings_df['days_since_start'] = warnings_df['days_since_start'].dt.days
        
        return warnings_df
    
    
    def calculate_lead_time(self, backtest_results, event_date, dd_threshold=2.0):
        """
        Calculate how many days before event the model warned
        
        Args:
            backtest_results (pd.DataFrame): Results from run_backtest
            event_date (str): Date of actual event (YYYY-MM-DD)
            dd_threshold (float): Warning threshold
        
        Returns:
            dict: Lead time analysis
        """
        event = pd.to_datetime(event_date)
        
        # Find first warning
        warnings = self.identify_warnings(backtest_results, dd_threshold)
        
        if warnings.empty:
            return {
                'first_warning_date': None,
                'lead_time_days': 0,
                'lead_time_weeks': 0,
                'had_warning': False,
            }
        
        first_warning_date = pd.to_datetime(warnings.iloc[0]['date'])
        lead_time_days = (event - first_warning_date).days
        
        return {
            'first_warning_date': first_warning_date.strftime('%Y-%m-%d'),
            'lead_time_days': lead_time_days,
            'lead_time_weeks': lead_time_days / 7,
            'had_warning': True,
            'min_dd_before_event': backtest_results['distance_to_default'].min(),
            'max_spread_before_event': backtest_results['theo_spread_bps'].max(),
        }
    
    
    def _classify_signal(self, dd, spread):
        """Classify signal based on distance to default and spread"""
        if dd < 0:
            return "CRITICAL - IMMINENT DEFAULT"
        elif dd < 1:
            return "SEVERE DISTRESS"
        elif dd < 2:
            return "WARNING"
        elif spread > SIGNAL_THRESHOLD_STRONG:
            return "SHORT CREDIT (Strong)"
        elif spread > SIGNAL_THRESHOLD_MODERATE:
            return "SHORT CREDIT (Moderate)"
        else:
            return "NEUTRAL"
    
    
    def _calculate_signal_strength(self, dd):
        """Calculate star rating based on DD"""
        if dd < 0:
            return "★★★★★"
        elif dd < 1:
            return "★★★★"
        elif dd < 2:
            return "★★★"
        elif dd < 3:
            return "★★"
        elif dd < 5:
            return "★"
        else:
            return ""


# ========== CONVENIENCE FUNCTIONS ==========

def run_backtest(ticker, start_date, end_date, frequency='weekly'):
    """
    Convenience function to run backtest
    
    Args:
        ticker (str): Stock ticker
        start_date (str): Start date
        end_date (str): End date
        frequency (str): Sampling frequency
    
    Returns:
        pd.DataFrame: Backtest results
    """
    runner = BacktestRunner(ticker)
    return runner.run_backtest(start_date, end_date, frequency)