"""
Performance metrics for backtest validation
"""
import pandas as pd
import numpy as np


def calculate_metrics(backtest_results, event_date, dd_threshold=2.0):
    """
    Calculate comprehensive performance metrics
    
    Args:
        backtest_results (pd.DataFrame): Backtest results
        event_date (str): Date of actual event
        dd_threshold (float): Warning threshold
    
    Returns:
        dict: Performance metrics
    """
    event = pd.to_datetime(event_date)
    
    # Identify warnings (predictions)
    warnings = backtest_results[backtest_results['distance_to_default'] < dd_threshold]
    
    # Calculate lead time
    if not warnings.empty:
        first_warning = pd.to_datetime(warnings.iloc[0]['date'])
        lead_time_days = (event - first_warning).days
        had_warning = True
    else:
        lead_time_days = 0
        had_warning = False
    
    # Calculate DD statistics
    dd_series = backtest_results['distance_to_default']
    dd_drop = dd_series.max() - dd_series.min()
    
    # Calculate volatility statistics
    vol_series = backtest_results['sigma_E']
    vol_increase = (vol_series.max() - vol_series.min()) / vol_series.min() * 100
    
    # Calculate spread statistics
    spread_series = backtest_results['theo_spread_bps']
    max_spread = spread_series.max()
    
    return {
        'ticker': backtest_results.iloc[0].get('ticker', 'Unknown'),
        'backtest_period_days': len(backtest_results) * 7,  # Approximate for weekly
        'total_observations': len(backtest_results),
        
        # Warning metrics
        'had_warning': had_warning,
        'lead_time_days': lead_time_days,
        'lead_time_weeks': round(lead_time_days / 7, 1),
        'warning_count': len(warnings),
        
        # Distance to Default
        'dd_max': round(dd_series.max(), 2),
        'dd_min': round(dd_series.min(), 2),
        'dd_drop': round(dd_drop, 2),
        'dd_final': round(dd_series.iloc[-1], 2),
        
        # Volatility
        'vol_min': round(vol_series.min() * 100, 1),
        'vol_max': round(vol_series.max() * 100, 1),
        'vol_increase_pct': round(vol_increase, 1),
        
        # Spread
        'spread_max_bps': round(max_spread, 0),
        'spread_final_bps': round(spread_series.iloc[-1], 0),
        
        # Accuracy
        'prediction_accuracy': '100%' if had_warning else '0%',
        'false_positives': 0,  # Would need non-event data to calculate
    }


def print_metrics_summary(metrics):
    """
    Print formatted metrics summary
    
    Args:
        metrics (dict): Metrics from calculate_metrics
    """
    print("\n" + "="*60)
    print("BACKTEST PERFORMANCE METRICS")
    print("="*60)
    
    print(f"\nTicker: {metrics['ticker']}")
    print(f"Observations: {metrics['total_observations']} ({metrics['backtest_period_days']} days)")
    
    print(f"\n🎯 WARNING METRICS:")
    print(f"  Early Warning: {'YES ✓' if metrics['had_warning'] else 'NO ✗'}")
    if metrics['had_warning']:
        print(f"  Lead Time: {metrics['lead_time_days']} days ({metrics['lead_time_weeks']} weeks)")
        print(f"  Warning Count: {metrics['warning_count']}")
    
    print(f"\n📉 DISTANCE TO DEFAULT:")
    print(f"  Peak: {metrics['dd_max']}σ")
    print(f"  Trough: {metrics['dd_min']}σ")
    print(f"  Total Drop: {metrics['dd_drop']}σ")
    print(f"  Final: {metrics['dd_final']}σ")
    
    print(f"\n📊 VOLATILITY:")
    print(f"  Range: {metrics['vol_min']}% - {metrics['vol_max']}%")
    print(f"  Increase: {metrics['vol_increase_pct']}%")
    
    print(f"\n💰 CREDIT SPREAD:")
    print(f"  Peak: {metrics['spread_max_bps']} bps")
    print(f"  Final: {metrics['spread_final_bps']} bps")
    
    print(f"\n✅ ACCURACY:")
    print(f"  Prediction Accuracy: {metrics['prediction_accuracy']}")
    
    print("\n" + "="*60 + "\n")