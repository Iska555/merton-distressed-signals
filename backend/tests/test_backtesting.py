"""
Test backtesting framework with real historical cases
"""
from backtesting.backtest_runner import BacktestRunner
from backtesting.metrics import calculate_metrics, print_metrics_summary
import pandas as pd


def test_svb_backtest():
    """
    Test Silicon Valley Bank collapse prediction
    
    Event: March 10, 2023 - FDIC seizure
    """
    print("\n" + "="*70)
    print("CASE STUDY: SILICON VALLEY BANK (SVB) - March 2023 Collapse")
    print("="*70)
    
    ticker = "SIVB"  # SVB ticker (delisted after collapse)
    start_date = "2023-02-01"
    end_date = "2023-03-09"  # Day before collapse
    event_date = "2023-03-10"
    
    try:
        runner = BacktestRunner(ticker)
        results = runner.run_backtest(start_date, end_date, frequency='daily')
        
        # Calculate lead time
        lead_time = runner.calculate_lead_time(results, event_date, dd_threshold=2.0)
        
        print("\n📊 LEAD TIME ANALYSIS:")
        if lead_time['had_warning']:
            print(f"  ✓ First Warning: {lead_time['first_warning_date']}")
            print(f"  ✓ Lead Time: {lead_time['lead_time_days']} days ({lead_time['lead_time_weeks']:.1f} weeks)")
            print(f"  ✓ Min DD: {lead_time['min_dd_before_event']:.2f}σ")
        else:
            print("  ✗ No warning issued")
        
        # Calculate comprehensive metrics
        metrics = calculate_metrics(results, event_date)
        print_metrics_summary(metrics)
        
        # Save results
        results.to_csv('backtest_svb.csv', index=False)
        print("✓ Results saved to backtest_svb.csv")
        
        return results
    
    except Exception as e:
        print(f"\n✗ BACKTEST FAILED: {e}")
        print("\nNote: SVB (SIVB) was delisted after collapse.")
        print("Historical data may be limited or unavailable via yfinance.")
        return None


def test_bbby_backtest():
    """
    Test Bed Bath & Beyond bankruptcy prediction
    
    Event: April 23, 2023 - Chapter 11 filing
    """
    print("\n" + "="*70)
    print("CASE STUDY: BED BATH & BEYOND (BBBY) - 2022-2023 Bankruptcy")
    print("="*70)
    
    ticker = "BBBY"  # Delisted after bankruptcy
    start_date = "2022-10-01"
    end_date = "2023-04-20"
    event_date = "2023-04-23"
    
    try:
        runner = BacktestRunner(ticker)
        results = runner.run_backtest(start_date, end_date, frequency='weekly')
        
        # Calculate lead time
        lead_time = runner.calculate_lead_time(results, event_date, dd_threshold=2.0)
        
        print("\n📊 LEAD TIME ANALYSIS:")
        if lead_time['had_warning']:
            print(f"  ✓ First Warning: {lead_time['first_warning_date']}")
            print(f"  ✓ Lead Time: {lead_time['lead_time_days']} days ({lead_time['lead_time_weeks']:.1f} weeks)")
        else:
            print("  ✗ No warning issued")
        
        # Calculate metrics
        metrics = calculate_metrics(results, event_date)
        print_metrics_summary(metrics)
        
        # Save results
        results.to_csv('backtest_bbby.csv', index=False)
        print("✓ Results saved to backtest_bbby.csv")
        
        return results
    
    except Exception as e:
        print(f"\n✗ BACKTEST FAILED: {e}")
        return None


def test_wework_backtest():
    """
    Test WeWork IPO failure prediction
    
    Event: September 30, 2019 - IPO cancelled
    """
    print("\n" + "="*70)
    print("CASE STUDY: WEWORK (WE) - 2019 IPO Collapse")
    print("="*70)
    
    # Note: WeWork didn't IPO until 2021 via SPAC
    # For 2019, we'd need private market data which isn't available
    print("\n⚠️  WeWork was private in 2019 - no public equity data available")
    print("Skipping this backtest (would require private market data)")
    
    return None


if __name__ == "__main__":
    # Run all backtests
    print("\n🚀 STARTING BACKTESTING SUITE\n")
    
    svb_results = test_svb_backtest()
    bbby_results = test_bbby_backtest()
    wework_results = test_wework_backtest()
    
    print("\n" + "="*70)
    print("✓ BACKTESTING COMPLETE")
    print("="*70)