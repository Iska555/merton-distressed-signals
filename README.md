# 📉 Merton Distressed Signal Generator



A quantitative credit risk tool that identifies mispriced corporate bonds by reverse-engineering the **Merton Structural Model**.



### 🎯 The Objective



The market often misprices corporate credit because bond liquidity is lower than equity liquidity. This project uses the **Black-Scholes-Merton** framework to treat a company's equity as a call option on its assets. By solving for unobservable asset value and volatility, we calculate a **"Fair Value" Credit Spread** and compare it to market yields to find alpha.



---



### 🛠 The Engine (Phase 1: Complete ✅)



The core mathematical module is built to handle the non-linear relationship between equity and debt.



* **Multi-Start Hybrid Solver:** Uses a sophisticated iterative approach (fsolve + L-BFGS-B) with multiple initial guesses to ensure convergence even for highly distressed or leveraged capital structures.

* **Risk-Aware Fallback:** Implements a 15% Asset Volatility floor for firms where , preventing the "False Safe" signal often found in naive Merton implementations.

* **Distance to Default (DD):** Calculates how many standard deviations a firm is from insolvency.

* **Theoretical Spread:** Converts default probabilities into a "Fair Value" credit spread in basis points (bps).



---



### 📡 Data & Market Intelligence (Phase 2 & 3: Complete ✅)



The tool now interacts with real-world financial markets to ground its theoretical outputs.



* **Equity Pipeline:** Automated fetching of Market Cap (), Total Debt (), and Equity Volatility () using `yfinance`.

* **Volatility Logic:** Prioritizes forward-looking Implied Volatility (IV) from option chains, falling back to 60-day realized volatility when necessary.

* **Market Benchmarks:** Integrated with **FRED API** to pull real-time ICE BofA Option-Adjusted Spreads (OAS).

* **Synthetic Ratings:** Includes a heuristic engine that estimates credit ratings based on market-implied leverage () to provide accurate market comparisons.



---



### 🗺 Project Roadmap



* [x] **Phase 1: The Merton Engine** (Mathematical Core & Robust Solver)

* [x] **Phase 2: Data Pipeline** (Real-time integration with `yfinance`)

* [x] **Phase 3: Market Spread Fetcher** (Live benchmark yields via FRED API)

* [ ] **Phase 4: Signal Generator** (Alpha Generation: Theoretical vs. Market)

* [ ] **Phase 5: Sensitivity Analysis** (Greeks & Stress Testing)

* [ ] **Phase 6: Full-Stack Web App** (FastAPI + Next.js Deployment)



---



### 🚀 Usage Example



```python

# Analyze a live ticker (e.g., Ford Motor Company)

from data.equity_fetcher import EquityDataFetcher

from signals.generator import MertonSignalGenerator



# Fetch real-time data and generate signal

generator = MertonSignalGenerator()

analysis = generator.analyze_ticker("F")



print(f"Ticker: {analysis['ticker']}")

print(f"Merton Fair Value: {analysis['merton_spread']} bps")

print(f"Market Reality: {analysis['market_spread']} bps")

print(f"Signal: {analysis['signal']}")



```



---



### 📊 Tech Stack



* **Language:** Python 3.10+

* **Math/Stats:** NumPy, SciPy, Pandas

* **APIs:** yfinance, FRED (Federal Reserve Economic Data)

* **DevOps:** Dotenv (Secure API Management), Git



---



### Current Status



**Last Updated:** February 2, 2026

**Status:** Backend logic and data pipes fully functional. Moving to Signal Aggregation and Web Layer.



---