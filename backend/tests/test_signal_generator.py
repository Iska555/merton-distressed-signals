"""
Test signal generator
"""
from signals.generator import SignalGenerator, analyze_company
import pandas as pd


def test_single_company():
    """Test analyzing a single company"""
    print("\n" + "="*60)
    print("TEST: Single Company Analysis")
    print("="*60 + "\n")
    
    result = analyze_company('AAPL', verbose=True)
    
    # Verify required fields
    assert 'ticker' in result
    assert 'signal' in result
    assert 'theo_spread_bps' in result
    assert 'market_spread_bps' in result
    
    print("\n✓ Single company analysis works")
    
    return result


def test_batch_analysis():
    """Test analyzing multiple companies"""
    print("\n" + "="*60)
    print("TEST: Batch Analysis")
    print("="*60 + "\n")
    
    test_tickers = ['AAPL', 'TSLA', 'MSFT', 'F', 'BAC']
    
    generator = SignalGenerator()
    df = generator.analyze_batch(test_tickers, verbose=True)
    
    print("\nRESULTS SUMMARY:")
    print("="*60)
    
    if not df.empty:
        summary = df[[
            'ticker', 
            'company_name',
            'distance_to_default',
            'theo_spread_bps',
            'market_spread_bps',
            'spread_diff_bps',
            'signal',
            'signal_strength'
        ]]
        
        print(summary.to_string(index=False))
    
    print("\n✓ Batch analysis works")
    
    return df


def test_top_signals():
    """Test extracting top signals"""
    print("\n" + "="*60)
    print("TEST: Top Signals Extraction")
    print("="*60 + "\n")
    
    test_tickers = [
        'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN',
        'F', 'GM', 'BAC', 'JPM', 'C'
    ]
    
    generator = SignalGenerator()
    df = generator.analyze_batch(test_tickers, verbose=False)
    
    if df.empty:
        print("⚠ No results to extract signals from")
        return
    
    top_signals = generator.get_top_signals(df, n=3)
    
    print("TOP 3 LONG CREDIT OPPORTUNITIES:")
    print("-" * 60)
    if not top_signals['long'].empty:
        long_summary = top_signals['long'][[
            'ticker',
            'spread_diff_bps',
            'signal',
            'signal_strength'
        ]]
        print(long_summary.to_string(index=False))
    else:
        print("No long signals found")
    
    print("\nTOP 3 SHORT CREDIT OPPORTUNITIES:")
    print("-" * 60)
    if not top_signals['short'].empty:
        short_summary = top_signals['short'][[
            'ticker',
            'spread_diff_bps',
            'signal',
            'signal_strength'
        ]]
        print(short_summary.to_string(index=False))
    else:
        print("No short signals found")
    
    print("\n✓ Signal extraction works")


def test_signal_classification():
    """Test signal classification logic"""
    print("\n" + "="*60)
    print("TEST: Signal Classification")
    print("="*60 + "\n")
    
    generator = SignalGenerator()
    
    test_cases = [
        (200, "SHORT CREDIT", "Strong short"),
        (100, "SHORT CREDIT (Moderate)", "Moderate short"),
        (50, "NEUTRAL", "Neutral"),
        (-100, "LONG CREDIT (Moderate)", "Moderate long"),
        (-200, "LONG CREDIT", "Strong long"),
    ]
    
    for spread_diff, expected_signal, description in test_cases:
        signal = generator._classify_signal(spread_diff)
        strength = generator._calculate_signal_strength(spread_diff)
        
        print(f"{spread_diff:+4d} bps → {signal:30s} {strength:10s} ({description})")
        
        assert expected_signal in signal
    
    print("\n✓ Signal classification works correctly")


if __name__ == "__main__":
    test_single_company()
    test_batch_analysis()
    test_top_signals()
    test_signal_classification()
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("="*60)