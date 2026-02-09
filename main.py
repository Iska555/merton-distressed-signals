"""
Command-line interface for Merton Signal Generator
"""
import sys
import argparse
from signals.generator import SignalGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Merton Credit Signal Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py AAPL              # Analyze single company
  python main.py AAPL TSLA MSFT    # Analyze multiple companies
  python main.py --batch sp500.txt # Analyze from file
        """
    )
    
    parser.add_argument(
        'tickers',
        nargs='*',
        help='Stock tickers to analyze'
    )
    
    parser.add_argument(
        '--batch',
        type=str,
        help='File containing list of tickers (one per line)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Save results to CSV file'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Number of top signals to show (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Get tickers
    tickers = args.tickers
    
    if args.batch:
        with open(args.batch, 'r') as f:
            batch_tickers = [line.strip() for line in f if line.strip()]
            tickers.extend(batch_tickers)
    
    if not tickers:
        parser.print_help()
        sys.exit(1)
    
    # Run analysis
    generator = SignalGenerator()
    
    if len(tickers) == 1:
        # Single company
        result = generator.analyze_single(tickers[0], verbose=True)
    else:
        # Batch
        df = generator.analyze_batch(tickers, verbose=True)
        
        if not df.empty:
            # Show top signals
            top_signals = generator.get_top_signals(df, n=args.top)
            
            print("\n" + "="*60)
            print(f"TOP {args.top} SIGNALS")
            print("="*60)
            
            if not top_signals['short'].empty:
                print("\n🔴 SHORT CREDIT OPPORTUNITIES:")
                print(top_signals['short'][[
                    'ticker', 'theo_spread_bps', 'market_spread_bps',
                    'spread_diff_bps', 'signal_strength'
                ]].to_string(index=False))
            
            if not top_signals['long'].empty:
                print("\n🟢 LONG CREDIT OPPORTUNITIES:")
                print(top_signals['long'][[
                    'ticker', 'theo_spread_bps', 'market_spread_bps',
                    'spread_diff_bps', 'signal_strength'
                ]].to_string(index=False))
            
            # Save to CSV if requested
            if args.output:
                df.to_csv(args.output, index=False)
                print(f"\n✓ Results saved to {args.output}")
    

    parser.add_argument(
    '--sensitivity',
    action='store_true',
    help='Run sensitivity analysis on results'
)

# After single company analysis, add:
    if args.sensitivity and 'error' not in result:
        from signals.sensitivity import analyze_sensitivity
    
        base_inputs = {
            'E': result['E'],
            'D': result['D'],
            'sigma_E': result['sigma_E'],
            'r': result['r'],
            'T': result['T']
        }
    
        analyze_sensitivity(
            base_inputs,
            result['market_spread_bps'],
            ticker=result['ticker'],
            verbose=True
        )


if __name__ == "__main__":
    main()