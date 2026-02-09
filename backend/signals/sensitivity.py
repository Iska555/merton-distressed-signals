"""
Sensitivity analysis for Merton credit signals

Tests signal robustness under:
- Volatility shocks (±20%)
- Debt shocks (±20%)
- Combined stress scenarios

Helps identify which signals are stable vs. fragile
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
    merton_credit_spread
)


class SensitivityAnalyzer:
    """
    Perform sensitivity analysis on Merton signals
    
    Tests how theoretical spreads change when inputs are shocked
    """
    
    def __init__(self, base_inputs):
        """
        Initialize analyzer with base case inputs
        
        Args:
            base_inputs (dict): Must contain {E, D, sigma_E, r, T}
        """
        self.base = base_inputs
        
        # Validate inputs
        required = ['E', 'D', 'sigma_E', 'r', 'T']
        for key in required:
            if key not in base_inputs:
                raise ValueError(f"Missing required input: {key}")
    
    
    def volatility_sensitivity(self, shocks=None):
        """
        Test sensitivity to equity volatility shocks
        
        Args:
            shocks (list): List of shock percentages (e.g., [-0.2, 0, 0.2])
        
        Returns:
            pd.DataFrame: Results for each shock scenario
        """
        if shocks is None:
            shocks = [-0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30]
        
        results = []
        base_sigma = self.base['sigma_E']
        
        for shock in shocks:
            shocked_sigma = base_sigma * (1 + shock)
            
            try:
                # Solve Merton with shocked volatility
                V, sigma_V, method = solve_merton_system(
                    E=self.base['E'],
                    sigma_E=shocked_sigma,
                    D=self.base['D'],
                    r=self.base['r'],
                    T=self.base['T']
                )
                
                # Calculate metrics
                dd = merton_distance_to_default(
                    V, sigma_V, self.base['D'], self.base['r'], self.base['T']
                )
                
                spread = merton_credit_spread(
                    V, sigma_V, self.base['D'], self.base['r'], self.base['T']
                )
                
                results.append({
                    'shock_pct': shock * 100,
                    'sigma_E': shocked_sigma,
                    'V': V,
                    'sigma_V': sigma_V,
                    'distance_to_default': dd,
                    'theo_spread_bps': spread,
                    'solver_method': method
                })
            
            except Exception as e:
                warnings.warn(f"Volatility shock {shock:.1%} failed: {e}")
                results.append({
                    'shock_pct': shock * 100,
                    'sigma_E': shocked_sigma,
                    'V': np.nan,
                    'sigma_V': np.nan,
                    'distance_to_default': np.nan,
                    'theo_spread_bps': np.nan,
                    'solver_method': 'failed'
                })
        
        df = pd.DataFrame(results)
        
        # Calculate spread change from base case
        base_spread = df[df['shock_pct'] == 0]['theo_spread_bps'].values[0]
        df['spread_change_bps'] = df['theo_spread_bps'] - base_spread
        
        return df
    
    
    def debt_sensitivity(self, shocks=None):
        """
        Test sensitivity to debt level shocks
        
        Args:
            shocks (list): List of shock percentages
        
        Returns:
            pd.DataFrame: Results for each shock scenario
        """
        if shocks is None:
            shocks = [-0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30]
        
        results = []
        base_debt = self.base['D']
        
        for shock in shocks:
            shocked_debt = base_debt * (1 + shock)
            
            try:
                # Solve Merton with shocked debt
                V, sigma_V, method = solve_merton_system(
                    E=self.base['E'],
                    sigma_E=self.base['sigma_E'],
                    D=shocked_debt,
                    r=self.base['r'],
                    T=self.base['T']
                )
                
                # Calculate metrics
                dd = merton_distance_to_default(
                    V, sigma_V, shocked_debt, self.base['r'], self.base['T']
                )
                
                spread = merton_credit_spread(
                    V, sigma_V, shocked_debt, self.base['r'], self.base['T']
                )
                
                leverage = shocked_debt / V if V > 0 else np.nan
                
                results.append({
                    'shock_pct': shock * 100,
                    'D': shocked_debt,
                    'V': V,
                    'leverage': leverage,
                    'distance_to_default': dd,
                    'theo_spread_bps': spread,
                    'solver_method': method
                })
            
            except Exception as e:
                warnings.warn(f"Debt shock {shock:.1%} failed: {e}")
                results.append({
                    'shock_pct': shock * 100,
                    'D': shocked_debt,
                    'V': np.nan,
                    'leverage': np.nan,
                    'distance_to_default': np.nan,
                    'theo_spread_bps': np.nan,
                    'solver_method': 'failed'
                })
        
        df = pd.DataFrame(results)
        
        # Calculate spread change from base case
        base_spread = df[df['shock_pct'] == 0]['theo_spread_bps'].values[0]
        df['spread_change_bps'] = df['theo_spread_bps'] - base_spread
        
        return df
    
    
    def combined_stress_test(self):
        """
        Run combined stress scenarios
        
        Tests worst-case combinations:
        - High vol + High debt (stress scenario)
        - Low vol + Low debt (benign scenario)
        
        Returns:
            pd.DataFrame: Stress test results
        """
        scenarios = [
            {'name': 'Base Case', 'vol_shock': 0.0, 'debt_shock': 0.0},
            {'name': 'Mild Stress', 'vol_shock': 0.10, 'debt_shock': 0.10},
            {'name': 'Moderate Stress', 'vol_shock': 0.20, 'debt_shock': 0.20},
            {'name': 'Severe Stress', 'vol_shock': 0.30, 'debt_shock': 0.30},
            {'name': 'Extreme Stress', 'vol_shock': 0.50, 'debt_shock': 0.30},
            {'name': 'Benign', 'vol_shock': -0.20, 'debt_shock': -0.20},
        ]
        
        results = []
        
        for scenario in scenarios:
            shocked_sigma = self.base['sigma_E'] * (1 + scenario['vol_shock'])
            shocked_debt = self.base['D'] * (1 + scenario['debt_shock'])
            
            try:
                V, sigma_V, method = solve_merton_system(
                    E=self.base['E'],
                    sigma_E=shocked_sigma,
                    D=shocked_debt,
                    r=self.base['r'],
                    T=self.base['T']
                )
                
                dd = merton_distance_to_default(
                    V, sigma_V, shocked_debt, self.base['r'], self.base['T']
                )
                
                spread = merton_credit_spread(
                    V, sigma_V, shocked_debt, self.base['r'], self.base['T']
                )
                
                results.append({
                    'scenario': scenario['name'],
                    'vol_shock_pct': scenario['vol_shock'] * 100,
                    'debt_shock_pct': scenario['debt_shock'] * 100,
                    'sigma_E': shocked_sigma,
                    'D': shocked_debt,
                    'distance_to_default': dd,
                    'theo_spread_bps': spread,
                    'solver_method': method
                })
            
            except Exception as e:
                warnings.warn(f"Stress scenario '{scenario['name']}' failed: {e}")
                results.append({
                    'scenario': scenario['name'],
                    'vol_shock_pct': scenario['vol_shock'] * 100,
                    'debt_shock_pct': scenario['debt_shock'] * 100,
                    'sigma_E': shocked_sigma,
                    'D': shocked_debt,
                    'distance_to_default': np.nan,
                    'theo_spread_bps': np.nan,
                    'solver_method': 'failed'
                })
        
        return pd.DataFrame(results)
    
    
    def check_signal_robustness(self, market_spread, threshold=75):
        """
        Check if signal is robust across volatility scenarios
        
        A signal is considered robust if it doesn't flip direction
        under ±20% volatility shocks
        
        Args:
            market_spread (float): Market spread in bps
            threshold (float): Signal threshold in bps
        
        Returns:
            dict: Robustness analysis
        """
        # Test volatility sensitivity
        vol_sens = self.volatility_sensitivity(shocks=[-0.20, -0.10, 0.0, 0.10, 0.20])
        
        # Get base case signal
        base_spread = vol_sens[vol_sens['shock_pct'] == 0]['theo_spread_bps'].values[0]
        base_diff = base_spread - market_spread
        base_signal = self._classify_signal(base_diff, threshold)
        
        # Check if signal flips under any shock
        flips = []
        for _, row in vol_sens.iterrows():
            if row['shock_pct'] == 0:
                continue
            
            shocked_diff = row['theo_spread_bps'] - market_spread
            shocked_signal = self._classify_signal(shocked_diff, threshold)
            
            if shocked_signal != base_signal and shocked_signal != 'NEUTRAL':
                flips.append({
                    'shock_pct': row['shock_pct'],
                    'original_signal': base_signal,
                    'new_signal': shocked_signal,
                    'spread_diff': shocked_diff
                })
        
        # Calculate spread volatility
        spread_std = vol_sens['theo_spread_bps'].std()
        spread_range = vol_sens['theo_spread_bps'].max() - vol_sens['theo_spread_bps'].min()
        
        is_robust = len(flips) == 0
        
        return {
            'is_robust': is_robust,
            'base_signal': base_signal,
            'base_spread_diff': base_diff,
            'signal_flips': flips,
            'spread_std': spread_std,
            'spread_range': spread_range,
            'vol_sensitivity_table': vol_sens
        }
    
    
    def generate_full_report(self, market_spread, ticker=None):
        """
        Generate comprehensive sensitivity report
        
        Args:
            market_spread (float): Market spread in bps
            ticker (str): Optional ticker symbol for labeling
        
        Returns:
            dict: Complete sensitivity analysis
        """
        report = {
            'ticker': ticker or 'Unknown',
            'timestamp': datetime.now().isoformat(),
            'base_inputs': self.base,
            'market_spread_bps': market_spread,
            'volatility_sensitivity': self.volatility_sensitivity(),
            'debt_sensitivity': self.debt_sensitivity(),
            'stress_test': self.combined_stress_test(),
            'robustness_check': self.check_signal_robustness(market_spread)
        }
        
        return report
    
    
    def _classify_signal(self, spread_diff, threshold=75):
        """
        Classify signal based on spread difference
        
        Args:
            spread_diff (float): Theoretical - Market spread
            threshold (float): Signal threshold in bps
        
        Returns:
            str: Signal classification
        """
        if spread_diff > threshold:
            return "SHORT CREDIT"
        elif spread_diff < -threshold:
            return "LONG CREDIT"
        else:
            return "NEUTRAL"
    
    
    def print_summary(self, market_spread, ticker=None):
        """
        Print human-readable sensitivity summary
        
        Args:
            market_spread (float): Market spread in bps
            ticker (str): Optional ticker symbol
        """
        print("\n" + "="*70)
        print(f"SENSITIVITY ANALYSIS: {ticker or 'Unknown'}")
        print("="*70)
        
        # Volatility sensitivity
        print("\nVOLATILITY SENSITIVITY:")
        print("-"*70)
        vol_sens = self.volatility_sensitivity()
        vol_display = vol_sens[['shock_pct', 'sigma_E', 'theo_spread_bps', 'spread_change_bps']]
        vol_display.columns = ['Vol Shock %', 'Sigma_E', 'Theo Spread', 'Change (bps)']
        print(vol_display.to_string(index=False))
        
        # Debt sensitivity
        print("\n\nDEBT SENSITIVITY:")
        print("-"*70)
        debt_sens = self.debt_sensitivity()
        debt_display = debt_sens[['shock_pct', 'D', 'leverage', 'theo_spread_bps', 'spread_change_bps']]
        debt_display.columns = ['Debt Shock %', 'Debt ($)', 'Leverage', 'Theo Spread', 'Change (bps)']
        print(debt_display.to_string(index=False))
        
        # Stress test
        print("\n\nSTRESS TEST SCENARIOS:")
        print("-"*70)
        stress = self.combined_stress_test()
        stress_display = stress[['scenario', 'vol_shock_pct', 'debt_shock_pct', 
                                  'distance_to_default', 'theo_spread_bps']]
        stress_display.columns = ['Scenario', 'Vol %', 'Debt %', 'DD', 'Spread (bps)']
        print(stress_display.to_string(index=False))
        
        # Robustness check
        print("\n\nSIGNAL ROBUSTNESS:")
        print("-"*70)
        robustness = self.check_signal_robustness(market_spread)
        
        print(f"Base Signal: {robustness['base_signal']}")
        print(f"Spread Diff: {robustness['base_spread_diff']:+.0f} bps")
        print(f"Robust: {'✓ YES' if robustness['is_robust'] else '✗ NO'}")
        print(f"Spread Range (±20% vol): {robustness['spread_range']:.0f} bps")
        print(f"Spread Std Dev: {robustness['spread_std']:.0f} bps")
        
        if robustness['signal_flips']:
            print("\n⚠ WARNING: Signal flips under these shocks:")
            for flip in robustness['signal_flips']:
                print(f"  {flip['shock_pct']:+.0f}% vol → {flip['new_signal']}")
        else:
            print("\n✓ Signal is stable across all volatility scenarios")
        
        print("\n" + "="*70 + "\n")


# ========== CONVENIENCE FUNCTIONS ==========

def analyze_sensitivity(ticker_inputs, market_spread, ticker=None, verbose=True):
    """
    Convenience function to run full sensitivity analysis
    
    Args:
        ticker_inputs (dict): Base inputs {E, D, sigma_E, r, T}
        market_spread (float): Market spread in bps
        ticker (str): Optional ticker symbol
        verbose (bool): Print summary
    
    Returns:
        dict: Full sensitivity report
    """
    analyzer = SensitivityAnalyzer(ticker_inputs)
    
    if verbose:
        analyzer.print_summary(market_spread, ticker)
    
    return analyzer.generate_full_report(market_spread, ticker)