"""
Command-line interface for Merton Signal Generator
"""
import sys
from data.equity_fetcher import EquityDataFetcher
from core.engine import (
    solve_merton_system,
    merton_distance_to_default,
    merton_credit_spread
)


def analyze_company(ticker):
    """Analyze a single company"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {ticker}")
    print(f"{'='*60}\n")
    
    # Fetch data
    fetcher = EquityDataFetcher(ticker)
    data = fetcher.fetch()
    
    # Run Merton model
    V, sigma_V, method = solve_merton_system(
        E=data['E'],
        sigma_E=data['sigma_E'],
        D=data['D'],
        r=data['r'],
        T=data['T']
    )
    
    dd = merton_distance_to_default(V, sigma_V, data['D'], data['r'], data['T'])
    spread = merton_credit_spread(V, sigma_V, data['D'], data['r'], data['T'])
    
    # Print results
    print(f"Company: {data['company_name']}")
    print(f"Sector:  {data['sector']}\n")
    
    print("INPUTS:")
    print(f"  Market Cap (E):  ${data['E']/1e9:.2f}B")
    print(f"  Total Debt (D):  ${data['D']/1e9:.2f}B")
    print(f"  Equity Vol:      {data['sigma_E']:.2%}\n")
    
    print("MERTON OUTPUTS:")
    print(f"  Asset Value (V):      ${V/1e9:.2f}B")
    print(f"  Asset Volatility:     {sigma_V:.2%}")
    print(f"  Leverage (D/V):       {data['D']/V:.2%}")
    print(f"  Distance to Default:  {dd:.2f}σ")
    print(f"  Theoretical Spread:   {spread:.0f} bps")
    print(f"  Solver Method:        {method}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py TICKER")
        print("Example: python main.py AAPL")
        sys.exit(1)
    
    ticker = sys.argv[1]
    analyze_company(ticker)