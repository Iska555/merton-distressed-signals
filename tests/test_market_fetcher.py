"""
Test market spread fetcher
"""
from data.market_fetcher import MarketSpreadFetcher, get_spread_table
import pandas as pd


def test_fetch_current_spreads():
    """Test fetching current spreads from FRED"""
    print("\n" + "="*60)
    print("TEST: Fetch Current Spreads")
    print("="*60 + "\n")
    
    fetcher = MarketSpreadFetcher()
    spreads = fetcher.get_current_spreads()
    
    print("Current Credit Spreads (OAS):\n")
    for rating, spread in spreads.items():
        if spread and rating not in ['IG_MASTER', 'HY_MASTER']:
            print(f"  {rating:4s}: {spread:6.1f} bps")
    
    # Verify we got data
    assert 'BBB' in spreads
    assert spreads['BBB'] is not None
    assert spreads['BBB'] > 0
    
    print("\n✓ Spreads fetched successfully")


def test_rating_estimation():
    """Test rating estimation from fundamentals"""
    print("\n" + "="*60)
    print("TEST: Rating Estimation")
    print("="*60 + "\n")
    
    fetcher = MarketSpreadFetcher()
    
    test_cases = [
        {'E': 3_000_000_000_000, 'D': 100_000_000_000, 'expected': 'AA'},  # Apple-like (low leverage)
        {'E': 100_000_000_000, 'D': 80_000_000_000, 'expected': 'BBB'},     # Moderate
        {'E': 50_000_000_000, 'D': 100_000_000_000, 'expected': 'B'},       # High leverage
        {'E': 10_000_000_000, 'D': 50_000_000_000, 'expected': 'CCC'},      # Distressed
    ]
    
    for case in test_cases:
        rating = fetcher.estimate_rating_from_fundamentals(case)
        leverage = case['D'] / (case['E'] + case['D'])
        
        print(f"Leverage: {leverage:.1%}  →  Rating: {rating}  (Expected: {case['expected']})")
        assert rating == case['expected']
    
    print("\n✓ Rating estimation works correctly")


def test_spread_by_rating():
    """Test getting spread for specific rating"""
    print("\n" + "="*60)
    print("TEST: Get Spread by Rating")
    print("="*60 + "\n")
    
    fetcher = MarketSpreadFetcher()
    
    ratings = ['AAA', 'A', 'BBB', 'BB', 'B', 'CCC']
    
    for rating in ratings:
        spread = fetcher.get_spread_by_rating(rating)
        print(f"  {rating}: {spread:.1f} bps")
        
        assert spread > 0
    
    print("\n✓ All ratings have valid spreads")


def test_company_spread():
    """Test getting market spread for real companies"""
    print("\n" + "="*60)
    print("TEST: Company Market Spreads")
    print("="*60 + "\n")
    
    fetcher = MarketSpreadFetcher()
    
    test_companies = [
        ('AAPL', {'E': 3_000_000_000_000, 'D': 100_000_000_000}),  # Safe
        ('TSLA', {'E': 800_000_000_000, 'D': 15_000_000_000}),     # Volatile
        ('F', {'E': 50_000_000_000, 'D': 100_000_000_000}),        # Leveraged
    ]
    
    for ticker, data in test_companies:
        rating = fetcher.get_company_rating(ticker, data)
        spread = fetcher.get_market_spread(ticker, data)
        
        print(f"{ticker:5s} → Rating: {rating:4s} → Spread: {spread:6.1f} bps")
        
        assert spread > 0
    
    print("\n✓ Company spreads fetched successfully")


def test_spread_table():
    """Test spread summary table"""
    print("\n" + "="*60)
    print("TEST: Spread Summary Table")
    print("="*60 + "\n")
    
    df = get_spread_table()
    
    print(df.to_string(index=False))
    
    assert not df.empty
    assert 'Rating' in df.columns
    assert 'Spread (bps)' in df.columns
    
    print("\n✓ Summary table generated")


if __name__ == "__main__":
    test_fetch_current_spreads()
    test_rating_estimation()
    test_spread_by_rating()
    test_company_spread()
    test_spread_table()
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("="*60)