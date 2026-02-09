from scipy.optimize import fsolve, minimize
import numpy as np
from scipy.stats import norm
import warnings


def solve_merton_system(E, sigma_E, D, r, T, method='hybrid'):
    """
    Reverse-engineer Asset Value (V) and Asset Volatility (sigma_V)
    from observable Equity Value (E) and Equity Volatility (sigma_E).
    
    The Merton model treats equity as a call option on firm assets:
    - Strike Price = Debt (D)
    - Underlying = Assets (V)
    - Volatility = Asset Volatility (sigma_V)
    
    Args:
        E (float): Market cap (equity value)
        sigma_E (float): Equity volatility (from options or historical)
        D (float): Total debt (face value)
        r (float): Risk-free rate
        T (float): Time horizon (typically 1 year)
        method (str): 'fsolve' | 'optimize' | 'hybrid'
    
    Returns:
        tuple: (V, sigma_V, solver_method)
            - V: Implied asset value
            - sigma_V: Implied asset volatility
            - solver_method: 'fsolve' | 'optimize' | 'fallback'
    """
    
# ========== STEP 1: Defining the System of Equations ==========
    def equations(vars):
        V, sigma_V = vars
        if V <= 0 or sigma_V <= 0:
            return [1e10, 1e10]
        
        try:
            d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
            d2 = d1 - sigma_V * np.sqrt(T)
            
            theoretical_E = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
            
            if E <= 0:
                return [1e10, 1e10]
            
            theoretical_sigma_E = (V / E) * norm.cdf(d1) * sigma_V
            return [theoretical_E - E, theoretical_sigma_E - sigma_E]
        except (ValueError, ZeroDivisionError, OverflowError):
            return [1e10, 1e10]

    def objective(vars):
        eq = equations(vars)
        return eq[0]**2 + eq[1]**2

    # ========== STEP 2: Multi-Guess Strategy (MODIFIED) ==========
    # We try multiple starting points to handle both safe and distressed firms
    guesses = [
        [E + D, sigma_E * (E / (E + D))],            # Standard Guess
        [E + D * 0.8, 0.25],                        # Distressed Guess (Assets closer to Debt)
        [E + D * 0.5, sigma_E * 0.5],               # High Leverage Guess
        [E + D, 0.40]                               # High Volatility Guess
    ]
    
    # ========== STEP 3 & 4: Iterative Solver (MODIFIED) ==========
    for initial_guess in guesses:
        # Try fsolve
        if method in ['fsolve', 'hybrid']:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    solution = fsolve(equations, initial_guess, full_output=True)
                    V, sigma_V = solution[0]
                    residuals = np.abs(solution[1]['fvec'])
                    
                    if np.all(residuals < 1e-6) and V > 0 and sigma_V > 0:
                        return V, sigma_V, 'fsolve'
            except:
                continue

        # Try Optimization if fsolve fails
        if method in ['optimize', 'hybrid']:
            try:
                bounds = [(E * 0.1, (E + D) * 5), (0.01, 3.0)]
                result = minimize(objective, x0=initial_guess, method='L-BFGS-B', 
                                  bounds=bounds, options={'ftol': 1e-9})
                if result.success and result.fun < 1e-4:
                    V, sigma_V = result.x
                    if V > 0 and sigma_V > 0:
                        return V, sigma_V, 'optimize'
            except:
                continue

    # ========== STEP 5: Improved Fallback (MODIFIED) ==========
    # If all solvers fail, we ensure sigma_V isn't unrealistically low for distressed names
    V_fallback = E + D
    naive_sigma_V = sigma_E * (E / (E + D)) if (E + D) > 0 else 0.2
    
    # If Equity is significantly smaller than Debt, firm is distressed. 
    # Floor the asset volatility at 15% to prevent underestimating risk.
    if E < D:
        sigma_V_fallback = max(0.15, naive_sigma_V)
    else:
        sigma_V_fallback = max(0.01, naive_sigma_V)
        
    return V_fallback, sigma_V_fallback, 'fallback'

def merton_distance_to_default(V, sigma_V, D, r, T):
    if np.isnan(V) or np.isnan(sigma_V) or V <= 0 or sigma_V <= 0:
        return np.nan
    try:
        numerator = np.log(V / D) + (r - 0.5 * sigma_V**2) * T
        denominator = sigma_V * np.sqrt(T)
        return numerator / denominator if denominator != 0 else np.nan
    except:
        return np.nan

def merton_default_probability(V, sigma_V, D, r, T):
    dd = merton_distance_to_default(V, sigma_V, D, r, T)
    return norm.cdf(-dd) if not np.isnan(dd) else np.nan

def merton_credit_spread(V, sigma_V, D, r, T, recovery_rate=0.4):
    PD = merton_default_probability(V, sigma_V, D, r, T)
    if np.isnan(PD): return np.nan
    LGD = 1.0 - recovery_rate
    expected_survival = 1.0 - (PD * LGD)
    if expected_survival <= 0: return 10000.0
    if expected_survival >= 1.0: return 0.0
    return -(1.0 / T) * np.log(expected_survival) * 10000.0