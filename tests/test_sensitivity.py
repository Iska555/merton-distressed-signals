"""
Test sensitivity analysis
"""
from signals.sensitivity import SensitivityAnalyzer, analyze_sensitivity
from signals.generator import analyze_company


def test_volatility_sensitivity():
    """Test volatility shock analysis"""
    print("\n" + "="*60)
    print("TEST: Volatility Sensitivity")
    print("="*60 + "\n")
    
    # Base case: Safe company
    base_inputs = {
        'E': 3_000_000_000_000,  # $3T
        'D': 100_000_000_000,    # $100B
        'sigma_E': 0.25,
        'r': 0.0352,
        'T': 1.0
    }
    
    analyzer = SensitivityAnalyzer(base_inputs)
    vol_sens = analyzer.volatility_sensitivity()
    
    print("Volatility Sensitivity Results:")
    print(vol_sens[['shock_pct', 'sigma_E', 'theo_spread_bps', 'spread_change_bps']].to_string(index=False))
    
    assert not vol_sens.empty
    assert 'theo_spread_bps' in vol_sens.columns
    
    print("\n✓ Volatility sensitivity works")


def test_debt_sensitivity():
    """Test debt shock analysis"""
    print("\n" + "="*60)
    print("TEST: Debt Sensitivity")
    print("="*60 + "\n")
    
    base_inputs = {
        'E': 800_000_000_000,
        'D': 15_000_000_000,
        'sigma_E': 0.52,
        'r': 0.0352,
        'T': 1.0
    }
    
    analyzer = SensitivityAnalyzer(base_inputs)
    debt_sens = analyzer.debt_sensitivity()
    
    print("Debt Sensitivity Results:")
    print(debt_sens[['shock_pct', 'D', 'leverage', 'theo_spread_bps']].to_string(index=False))
    
    assert not debt_sens.empty
    assert 'leverage' in debt_sens.columns
    
    print("\n✓ Debt sensitivity works")


def test_stress_scenarios():
    """Test combined stress scenarios"""
    print("\n" + "="*60)
    print("TEST: Stress Scenarios")
    print("="*60 + "\n")
    
    base_inputs = {
        'E': 500_000_000_000,
        'D': 80_000_000_000,
        'sigma_E': 0.40,
        'r': 0.0352,
        'T': 1.0
    }
    
    analyzer = SensitivityAnalyzer(base_inputs)
    stress = analyzer.combined_stress_test()
    
    print("Stress Test Results:")
    print(stress[['scenario', 'distance_to_default', 'theo_spread_bps']].to_string(index=False))
    
    assert not stress.empty
    assert 'scenario' in stress.columns
    
    print("\n✓ Stress testing works")


def test_signal_robustness():
    """Test signal robustness check"""
    print("\n" + "="*60)
    print("TEST: Signal Robustness")
    print("="*60 + "\n")
    
    # Robust signal (strong, stable)
    base_inputs = {
        'E': 3_000_000_000_000,
        'D': 100_000_000_000,
        'sigma_E': 0.25,
        'r': 0.0352,
        'T': 1.0
    }
    
    analyzer = SensitivityAnalyzer(base_inputs)
    market_spread = 200  # High market spread
    
    robustness = analyzer.check_signal_robustness(market_spread)
    
    print(f"Base Signal: {robustness['base_signal']}")
    print(f"Is Robust: {robustness['is_robust']}")
    print(f"Spread Range: {robustness['spread_range']:.0f} bps")
    
    if robustness['signal_flips']:
        print("\nSignal flips:")
        for flip in robustness['signal_flips']:
            print(f"  {flip['shock_pct']:+.0f}% → {flip['new_signal']}")
    
    assert 'is_robust' in robustness
    assert 'signal_flips' in robustness
    
    print("\n✓ Robustness checking works")


def test_full_report():
    """Test comprehensive sensitivity report"""
    print("\n" + "="*60)
    print("TEST: Full Sensitivity Report")
    print("="*60 + "\n")
    
    # Get real company data
    result = analyze_company('AAPL', verbose=False)
    
    if 'error' in result:
        print(f"⚠ Skipping test: {result['error']}")
        return
    
    # Run sensitivity analysis
    base_inputs = {
        'E': result['E'],
        'D': result['D'],
        'sigma_E': result['sigma_E'],
        'r': result['r'],
        'T': result['T']
    }
    
    report = analyze_sensitivity(
        base_inputs,
        result['market_spread_bps'],
        ticker='AAPL',
        verbose=True
    )
    
    assert 'volatility_sensitivity' in report
    assert 'debt_sensitivity' in report
    assert 'stress_test' in report
    assert 'robustness_check' in report
    
    print("✓ Full report generation works")


if __name__ == "__main__":
    test_volatility_sensitivity()
    test_debt_sensitivity()
    test_stress_scenarios()
    test_signal_robustness()
    test_full_report()
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("="*60)