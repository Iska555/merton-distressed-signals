"""
Test visualization functions
"""
from visualization.charts import (
    plot_spread_comparison,
    plot_volatility_sensitivity,
    plot_debt_sensitivity,
    plot_stress_test,
    plot_signal_dashboard
)
from signals.generator import SignalGenerator
from signals.sensitivity import SensitivityAnalyzer
import os


def test_spread_comparison():
    """Test spread comparison scatter plot"""
    print("\n" + "="*60)
    print("TEST: Spread Comparison Plot")
    print("="*60 + "\n")
    
    # Generate test data
    tickers = ['AAPL', 'TSLA', 'MSFT', 'F', 'BAC', 'JPM', 'GM', 'GOOGL']
    generator = SignalGenerator()
    df = generator.analyze_batch(tickers, verbose=False)
    
    if df.empty:
        print("⚠ No data to plot")
        return
    
    fig = plot_spread_comparison(df, save_path='output_spread_comparison.png', show=False)
    
    print("✓ Spread comparison plot created: output_spread_comparison.png")


def test_volatility_sensitivity_plot():
    """Test volatility sensitivity plot"""
    print("\n" + "="*60)
    print("TEST: Volatility Sensitivity Plot")
    print("="*60 + "\n")
    
    base_inputs = {
        'E': 800_000_000_000,
        'D': 15_000_000_000,
        'sigma_E': 0.52,
        'r': 0.0352,
        'T': 1.0
    }
    
    analyzer = SensitivityAnalyzer(base_inputs)
    vol_sens = analyzer.volatility_sensitivity()
    
    fig = plot_volatility_sensitivity(vol_sens, market_spread=285, 
                                       save_path='output_vol_sensitivity.png', show=False)
    
    print("✓ Volatility sensitivity plot created: output_vol_sensitivity.png")


def test_debt_sensitivity_plot():
    """Test debt sensitivity plot"""
    print("\n" + "="*60)
    print("TEST: Debt Sensitivity Plot")
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
    
    fig = plot_debt_sensitivity(debt_sens, save_path='output_debt_sensitivity.png', show=False)
    
    print("✓ Debt sensitivity plot created: output_debt_sensitivity.png")


def test_stress_test_plot():
    """Test stress test plot"""
    print("\n" + "="*60)
    print("TEST: Stress Test Plot")
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
    
    fig = plot_stress_test(stress, save_path='output_stress_test.png', show=False)
    
    print("✓ Stress test plot created: output_stress_test.png")


def test_signal_dashboard():
    """Test signal dashboard"""
    print("\n" + "="*60)
    print("TEST: Signal Dashboard")
    print("="*60 + "\n")
    
    # Generate larger dataset
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD',
        'F', 'GM', 'BAC', 'JPM', 'C', 'WFC', 'GS', 'MS'
    ]
    
    generator = SignalGenerator()
    df = generator.analyze_batch(tickers, verbose=False)
    
    if df.empty:
        print("⚠ No data to plot")
        return
    
    fig = plot_signal_dashboard(df, n_top=5, save_path='output_dashboard.png', show=False)
    
    print("✓ Signal dashboard created: output_dashboard.png")


if __name__ == "__main__":
    # Create output directory
    os.makedirs('visualization_outputs', exist_ok=True)
    os.chdir('visualization_outputs')
    
    test_spread_comparison()
    test_volatility_sensitivity_plot()
    test_debt_sensitivity_plot()
    test_stress_test_plot()
    test_signal_dashboard()
    
    print("\n" + "="*60)
    print("✓ ALL VISUALIZATION TESTS PASSED")
    print("="*60)
    print(f"\nOutput files saved in: {os.getcwd()}")