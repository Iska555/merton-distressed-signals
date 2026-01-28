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
        """
        Two equations, two unknowns: (V, sigma_V)
        
        Equation 1: E = V*N(d1) - D*exp(-rT)*N(d2)  [Black-Scholes]
        Equation 2: sigma_E = (V/E)*N(d1)*sigma_V   [Ito's Lemma]
        """
        V, sigma_V = vars
        
        # Bounds: Prevent negative/zero values during iteration
        if V <= 0 or sigma_V <= 0:
            return [1e10, 1e10]
        
        try:
            # Calculate d1 and d2 from Black-Scholes
            d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
            d2 = d1 - sigma_V * np.sqrt(T)
            
            # Equation 1: Black-Scholes formula for equity as call option
            theoretical_E = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
            
            # Equation 2: Volatility relationship (with zero-division protection)
            if E <= 0:
                return [1e10, 1e10]
            
            theoretical_sigma_E = (V / E) * norm.cdf(d1) * sigma_V
            
            # Return residuals (errors)
            return [theoretical_E - E, theoretical_sigma_E - sigma_E]
        
        except (ValueError, ZeroDivisionError, OverflowError):
            return [1e10, 1e10]
    
    
    def objective(vars):
        """Sum of squared errors for optimization fallback"""
        eq = equations(vars)
        return eq[0]**2 + eq[1]**2
    
    
    # ========== STEP 2: Initial Guess ==========
    # - V ≈ E + D (assets = equity + debt, book value approximation)
    # - sigma_V ≈ sigma_E * (E / (E+D)) (asset vol < equity vol due to leverage)
    
    V_guess = E + D * 0.8  # Conservative: assume some debt impairment
    sigma_V_guess = max(0.01, sigma_E * (E / (E + D)))  # Floor at 1% to avoid zero
    
    initial_guess = [V_guess, sigma_V_guess]
    
    
    # ========== STEP 3: Try fsolve (Fast Root Finder) ==========
    if method in ['fsolve', 'hybrid']:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                solution = fsolve(equations, initial_guess, full_output=True)
                V, sigma_V = solution[0]
                info = solution[1]
                
                # Check convergence quality
                residuals = np.abs(info['fvec'])
                converged = np.all(residuals < 1e-6)
                
                # Sanity checks
                if converged and V > 0 and sigma_V > 0 and V > E * 0.5:
                    return V, sigma_V, 'fsolve'
                
                # If poor convergence and hybrid mode, try optimization
                if method == 'fsolve':
                    raise ValueError("fsolve convergence failed")
        
        except Exception:
            if method == 'fsolve':
                # User explicitly requested fsolve only - fail
                return np.nan, np.nan, 'failed'
    
    
    # ========== STEP 4: Try Optimization (Robust but Slower) ==========
    if method in ['optimize', 'hybrid']:
        bounds = [
            (E * 0.3, E + D * 3),  # V bounds: floor at 30% of equity, ceiling at 3x book value
            (0.01, 3.0)            # sigma_V bounds: 1% to 300% (extreme range)
        ]
        
        try:
            result = minimize(
                objective,
                x0=initial_guess,
                method='L-BFGS-B',
                bounds=bounds,
                options={'ftol': 1e-9, 'maxiter': 500}
            )
            
            if result.success and result.fun < 1e-4:
                V, sigma_V = result.x
                
                # Final sanity check
                if V > 0 and sigma_V > 0:
                    return V, sigma_V, 'optimize'
        
        except Exception:
            pass
    
    
    # ========== STEP 5: Fallback ==========
    # If both solvers failed, return naive approximation
    
    V_fallback = E + D
    sigma_V_fallback = sigma_E * (E / (E + D)) if (E + D) > 0 else sigma_E * 0.5
    
    return V_fallback, sigma_V_fallback, 'fallback'


def merton_distance_to_default(V, sigma_V, D, r, T):
    """
    Calculate Merton's Distance-to-Default (DD)
    
    DD = (ln(V/D) + (r - 0.5*sigma_V^2)*T) / (sigma_V * sqrt(T))
    
    Interpretation: How many standard deviations is the firm above default?
    """
    if np.isnan(V) or np.isnan(sigma_V) or V <= 0 or sigma_V <= 0:
        return np.nan
    
    try:
        numerator = np.log(V / D) + (r - 0.5 * sigma_V**2) * T
        denominator = sigma_V * np.sqrt(T)
        
        if denominator == 0:
            return np.nan
        
        return numerator / denominator
    
    except (ValueError, ZeroDivisionError):
        return np.nan


def merton_default_probability(V, sigma_V, D, r, T):
    """
    Probability that firm assets fall below debt at time T
    
    PD = N(-DD) where N is the cumulative normal distribution
    """
    dd = merton_distance_to_default(V, sigma_V, D, r, T)
    
    if np.isnan(dd):
        return np.nan
    
    return norm.cdf(-dd)


def merton_credit_spread(V, sigma_V, D, r, T, recovery_rate=0.4):
    """
    Theoretical credit spread implied by Merton model
    
    Formula: Spread = -(1/T) * ln(1 - PD * LGD)
    
    Where:
    - PD = Probability of Default
    - LGD = Loss Given Default = (1 - Recovery Rate)
    
    Returns: Spread in basis points (bps)
    """
    # Calculate default probability
    PD = merton_default_probability(V, sigma_V, D, r, T)
    
    if np.isnan(PD):
        return np.nan
    
    # Define Loss Given Default
    LGD = 1.0 - recovery_rate
    
    # Expected survival probability
    expected_survival = 1.0 - (PD * LGD)
    
    # Handle edge cases
    if expected_survival <= 0:
        return 10000.0  # Cap at 10,000 bps (essentially defaulted)
    
    if expected_survival >= 1.0:
        return 0.0  # Risk-free
    
    # Calculate spread
    spread_decimal = -(1.0 / T) * np.log(expected_survival)
    
    # Convert to basis points
    spread_bps = spread_decimal * 10000.0
    
    return spread_bps