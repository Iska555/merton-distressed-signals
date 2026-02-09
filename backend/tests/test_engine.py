"""
Unit tests for Merton engine
"""
from core.engine import (
    solve_merton_system,
    merton_distance_to_default,
    merton_credit_spread
)


def test_safe_company():
    """Test Apple-like company (safe)"""
    E = 3_000_000_000_000  # $3T
    sigma_E = 0.25
    D = 100_000_000_000   # $100B
    r = 0.045
    T = 1.0
    
    V, sigma_V, method = solve_merton_system(E, sigma_E, D, r, T)
    
    print(f"\n=== SAFE COMPANY TEST ===")
    print(f"V: ${V/1e9:.1f}B")
    print(f"sigma_V: {sigma_V:.2%}")
    print(f"Method: {method}")
    
    dd = merton_distance_to_default(V, sigma_V, D, r, T)
    spread = merton_credit_spread(V, sigma_V, D, r, T)
    
    print(f"Distance to Default: {dd:.2f}σ")
    print(f"Credit Spread: {spread:.0f} bps")
    
    assert V > E
    assert dd > 5.0
    assert spread < 50


def test_distressed_company():
    """Test WeWork-like company (distressed)"""
    E = 500_000_000
    sigma_E = 0.95
    D = 8_000_000_000
    r = 0.045
    T = 1.0
    
    V, sigma_V, method = solve_merton_system(E, sigma_E, D, r, T)
    
    print(f"\n=== DISTRESSED COMPANY TEST ===")
    print(f"V: ${V/1e9:.1f}B")
    print(f"sigma_V: {sigma_V:.2%}")
    print(f"Method: {method}")
    
    dd = merton_distance_to_default(V, sigma_V, D, r, T)
    spread = merton_credit_spread(V, sigma_V, D, r, T)
    
    print(f"Distance to Default: {dd:.2f}σ")
    print(f"Credit Spread: {spread:.0f} bps")
    
    assert dd < 2.0
    assert spread > 500


if __name__ == "__main__":
    test_safe_company()
    test_distressed_company()
    print("\n✓ All tests passed!")