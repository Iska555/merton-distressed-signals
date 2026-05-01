"""
Merton Credit Signal Generator

Combines equity data, Merton model, and market spreads to generate
trading signals for credit arbitrage opportunities.
"""
import pandas as pd
import numpy as np
import warnings
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import (
    solve_merton_system,
    merton_distance_to_default,
    merton_default_probability,
    merton_credit_spread
)
from data.equity_fetcher import EquityDataFetcher
from data.market_fetcher import MarketSpreadFetcher
from config import (
    SIGNAL_THRESHOLD_STRONG,
    SIGNAL_THRESHOLD_MODERATE
)

# ── INSTITUTIONAL OVERRIDE CONSTANTS ──
BANK_SECTORS = {"Financial Services", "Banking", "Financial"}
SHADOW_BANKS = {"F", "GM", "BA"}  # Automakers with massive captive finance divisions


class SignalGenerator:
    """
    Generate credit trading signals by comparing theoretical vs market spreads
    
    Workflow:
    1. Fetch equity data (E, D, sigma_E)
    2. Solve Merton model (V, sigma_V)
    3. Calculate theoretical spread
    4. Get market spread
    5. Compare and generate signal
    """
    
    def __init__(self, fred_api_key=None):
        """
        Initialize signal generator
        
        Args:
            fred_api_key (str): FRED API key for market spreads
        """
        self.market_fetcher = MarketSpreadFetcher(api_key=fred_api_key)
    
    
    def analyze_single(self, ticker, verbose=True):
        """
        Analyze a single company with institutional structural overrides.
        
        Args:
            ticker (str): Stock ticker
            verbose (bool): Print progress messages
        
        Returns:
            dict: Complete analysis results
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"ANALYZING: {ticker}")
            print(f"{'='*60}\n")
        
        try:
            # STEP 1: Fetch equity data
            if verbose:
                print("Step 1: Fetching equity data...")
            
            equity_fetcher = EquityDataFetcher(ticker)
            equity_data = equity_fetcher.fetch()
            
            E = equity_data['E']
            raw_D = equity_data['D']
            sigma_E = equity_data['sigma_E']
            r = equity_data['r']
            T = equity_data['T']
            sector = equity_data.get('sector', 'Unknown')
            
            # ── BANK & SHADOW BANK OVERRIDE: STRUCTURAL DEBT ──
            if (sector in BANK_SECTORS or ticker in SHADOW_BANKS) and raw_D < (2.0 * E):
                D = max(E * 9.0, 1.0)
                if verbose:
                    print(f"  [!] OVERRIDE: Debt adjusted from ${raw_D/1e9:.2f}B to ${D/1e9:.2f}B")
            else:
                D = raw_D
            
            if verbose:
                print(f"  ✓ Market Cap: ${E/1e9:.2f}B")
                print(f"  ✓ Total Debt (Adjusted): ${D/1e9:.2f}B")
                print(f"  ✓ Equity Vol: {sigma_E:.2%}")
            
            # STEP 2: Solve Merton model
            if verbose:
                print("\nStep 2: Running Merton model...")
            
            V, sigma_V, method = solve_merton_system(E, sigma_E, D, r, T)
            
            if np.isnan(V) or np.isnan(sigma_V):
                raise ValueError("Merton solver failed to converge")
            
            if verbose:
                print(f"  ✓ Asset Value (V): ${V/1e9:.2f}B")
                print(f"  ✓ Asset Vol (σ_V): {sigma_V:.2%}")
                print(f"  ✓ Solver Method: {method}")
            
            # STEP 3: Calculate risk metrics
            if verbose:
                print("\nStep 3: Calculating risk metrics...")
            
            dd = merton_distance_to_default(V, sigma_V, D, r, T)
            pd = merton_default_probability(V, sigma_V, D, r, T)
            theo_spread = merton_credit_spread(V, sigma_V, D, r, T)
            
            # Calculate actual leverage using Merton-implied V
            actual_leverage = D / V
            
            if verbose:
                print(f"  ✓ Distance to Default: {dd:.2f}σ")
                print(f"  ✓ Default Probability: {pd:.2%}")
                print(f"  ✓ Theoretical Spread: {theo_spread:.0f} bps")
            
            # STEP 4: Get market spread using overrides
            if verbose:
                print("\nStep 4: Fetching market spread...")
            
            # Estimate rating using ACTUAL leverage (V, not E+D)
            rating = self._estimate_rating_from_merton_leverage(V, D)
            base_market_spread = self.market_fetcher.get_spread_by_rating(rating)
            
            # ── BANK & SHADOW BANK OVERRIDE: MARKET SPREAD ──
            mkt_cap_b = E / 1e9
            if sector in BANK_SECTORS or ticker in SHADOW_BANKS:
                if mkt_cap_b > 100: market_spread = 80.0
                elif mkt_cap_b > 10: market_spread = 120.0
                else: market_spread = 200.0
                if verbose: 
                    print(f"  [!] OVERRIDE: Spread locked to {market_spread:.0f} bps")
            else:
                market_spread = base_market_spread
            
            if verbose:
                print(f"  ✓ Estimated Rating: {rating}")
                if sector not in BANK_SECTORS and ticker not in SHADOW_BANKS:
                    print(f"  ✓ Market Spread: {market_spread:.0f} bps")
            
            # STEP 5: Generate signal
            if verbose:
                print("\nStep 5: Generating signal...")
            
            spread_diff = theo_spread - market_spread
            signal = self._classify_signal(spread_diff)
            signal_strength = self._calculate_signal_strength(spread_diff)
            
            if verbose:
                print(f"  ✓ Spread Difference: {spread_diff:+.0f} bps")
                print(f"  ✓ Signal: {signal} {signal_strength}")
            
            # STEP 6: Package results
            result = {
                # Identifiers
                'ticker': ticker,
                'company_name': equity_data['company_name'],
                'sector': sector,
                'industry': equity_data['industry'],
                'timestamp': datetime.now().isoformat(),
                
                # Equity inputs
                'E': E,
                'D': D,
                'sigma_E': sigma_E,
                'r': r,
                'T': T,
                
                # Merton outputs
                'V': V,
                'sigma_V': sigma_V,
                'leverage': actual_leverage,
                'distance_to_default': dd,
                'default_probability': pd,
                'theo_spread_bps': theo_spread,
                'solver_method': method,
                
                # Market data
                'estimated_rating': rating,
                'market_spread_bps': market_spread,
                
                # Signal
                'spread_diff_bps': spread_diff,
                'signal': signal,
                'signal_strength': signal_strength,
                
                # Data quality
                'volatility_source': equity_data['data_quality']['volatility_source'],
                'has_options': equity_data['data_quality']['has_options']
            }
            
            if verbose:
                print(f"\n{'='*60}")
                print(f"✓ ANALYSIS COMPLETE")
                print(f"{'='*60}\n")
            
            return result
        
        except Exception as e:
            if verbose:
                print(f"\n✗ ANALYSIS FAILED: {e}\n")
            
            return {
                'ticker': ticker,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    
    def analyze_batch(self, tickers, max_failures=0.3, verbose=True):
        """
        Analyze multiple companies
        
        Args:
            tickers (list): List of stock tickers
            max_failures (float): Max failure rate allowed (0-1)
            verbose (bool): Print progress
        
        Returns:
            pd.DataFrame: Results for all companies
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"BATCH ANALYSIS: {len(tickers)} companies")
            print(f"{'='*60}\n")
        
        results = []
        failures = []
        
        for i, ticker in enumerate(tickers, 1):
            if verbose:
                print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")
            
            try:
                result = self.analyze_single(ticker, verbose=False)
                
                if 'error' in result:
                    failures.append(ticker)
                    if verbose:
                        print(f"✗ Failed: {result['error']}")
                else:
                    results.append(result)
                    if verbose:
                        signal = result['signal']
                        strength = result['signal_strength']
                        print(f"✓ {signal} {strength}")
            
            except Exception as e:
                failures.append(ticker)
                if verbose:
                    print(f"✗ Error: {e}")
        
        # Check failure rate
        if len(tickers) > 0:
            failure_rate = len(failures) / len(tickers)
            if failure_rate > max_failures:
                warnings.warn(
                    f"High failure rate: {len(failures)}/{len(tickers)} "
                    f"({failure_rate:.1%})"
                )
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"BATCH COMPLETE: {len(results)} successes, {len(failures)} failures")
            print(f"{'='*60}\n")
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Sort by absolute spread difference (strongest signals first)
        df['abs_spread_diff'] = df['spread_diff_bps'].abs()
        df = df.sort_values('abs_spread_diff', ascending=False)
        df = df.drop('abs_spread_diff', axis=1)
        
        return df
    
    
    def get_top_signals(self, df, n=10, signal_type='both'):
        """
        Get top N signals from batch results
        
        Args:
            df (pd.DataFrame): Results from analyze_batch
            n (int): Number of top signals
            signal_type (str): 'long', 'short', or 'both'
        
        Returns:
            dict: {'long': df_long, 'short': df_short}
        """
        if df.empty:
            return {'long': pd.DataFrame(), 'short': pd.DataFrame()}
        
        # ── THE FIX: Hardcode 150 bps threshold to kill legacy config noise ──
        long_signals = df[df['spread_diff_bps'] < -150].copy()
        short_signals = df[df['spread_diff_bps'] > 150].copy()
        
        # Sort by magnitude
        long_signals = long_signals.sort_values('spread_diff_bps', ascending=True).head(n)
        short_signals = short_signals.sort_values('spread_diff_bps', ascending=False).head(n)
        
        if signal_type == 'long':
            return {'long': long_signals, 'short': pd.DataFrame()}
        elif signal_type == 'short':
            return {'long': pd.DataFrame(), 'short': short_signals}
        else:
            return {'long': long_signals, 'short': short_signals}
    
    
    def _estimate_rating_from_merton_leverage(self, V, D):
        """
        Refined rating heuristics for institutional and high-debt entities.
        """
        leverage = D / V
        
        # Institutional Tiers
        if leverage < 0.30: return 'AA'    # More room for high-quality debt
        elif leverage < 0.50: return 'A'
        elif leverage < 0.70: return 'BBB'
        elif leverage < 0.85: return 'BB'
        else: return 'CCC'
    
    
    def _classify_signal(self, spread_diff):
        """
        Classify trading signal based on spread difference
        Thresholds widened to keep standard safe yields as NEUTRAL.
        
        Args:
            spread_diff (float): Theoretical - Market spread (bps)
        
        Returns:
            str: Signal classification
        """
        if spread_diff > 300:
            return "SHORT CREDIT"
        elif spread_diff > 150:
            return "SHORT CREDIT (Moderate)"
        elif spread_diff < -300:
            return "LONG CREDIT"
        elif spread_diff < -150:
            return "LONG CREDIT (Moderate)"
        else:
            return "NEUTRAL"
    
    
    def _calculate_signal_strength(self, spread_diff):
        """
        Calculate signal strength as stars
        
        Args:
            spread_diff (float): Spread difference in bps
        
        Returns:
            str: Star rating
        """
        abs_diff = abs(spread_diff)
        
        if abs_diff > 300:
            return "★★★★★"
        elif abs_diff > 200:
            return "★★★★"
        elif abs_diff > 150:
            return "★★★"
        elif abs_diff > 75:
            return "★★"
        elif abs_diff > 25:
            return "★"
        else:
            return ""


# ========== CONVENIENCE FUNCTIONS ==========

def analyze_company(ticker, fred_api_key=None, verbose=True):
    """
    Convenience function to analyze a single company
    
    Args:
        ticker (str): Stock ticker
        fred_api_key (str): Optional FRED API key
        verbose (bool): Print progress
    
    Returns:
        dict: Analysis results
    """
    generator = SignalGenerator(fred_api_key=fred_api_key)
    return generator.analyze_single(ticker, verbose=verbose)


def analyze_batch(tickers, fred_api_key=None, verbose=True):
    """
    Convenience function to analyze multiple companies
    
    Args:
        tickers (list): List of tickers
        fred_api_key (str): Optional FRED API key
        verbose (bool): Print progress
    
    Returns:
        pd.DataFrame: Results
    """
    generator = SignalGenerator(fred_api_key=fred_api_key)
    return generator.analyze_batch(tickers, verbose=verbose)