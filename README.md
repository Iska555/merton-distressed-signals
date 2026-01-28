# 📉 Merton Distressed Signal Generator

A quantitative credit risk tool that identifies mispriced corporate bonds by reverse-engineering the **Merton Structural Model**.

### 🎯 The Objective

The market often misprices corporate credit because bond liquidity is lower than equity liquidity. This project uses the **Black-Scholes-Merton** framework to treat a company's equity as a call option on its assets. By solving for unobservable asset value and volatility, we calculate a **"Fair Value" Credit Spread** and compare it to market yields to find alpha.

---

### 🛠 The Engine (Phase 1: Complete ✅)

The core mathematical module is built to handle the non-linear relationship between equity and debt.

* **Implied Asset Solver:** A hybrid numerical approach using `scipy.optimize` (fsolve + L-BFGS-B) to back out  and .
* **Distance to Default (DD):** Calculates how many standard deviations a firm is from insolvency.
* **Probability of Default (PD):** Maps DD to a physical probability using the cumulative normal distribution.
* **Spread Generator:** Converts PD into a theoretical credit spread in basis points (bps).

---

### 🗺 Project Roadmap

* [x] **Phase 1: The Merton Engine** (Mathematical Core)
* [ ] **Phase 2: Data Pipeline** (Real-time integration with `yfinance`)
* [ ] **Phase 3: Market Spread Fetcher** (Benchmark yields via FRED API)
* [ ] **Phase 4: Signal Generator** (Theoretical vs. Market Arbitrage)
* [ ] **Phase 5: Backtesting** (Case Studies: SVB, Credit Suisse)

---

### 🚀 Quick Start (Mockup)

```python
from core.engine import solve_merton_system, merton_credit_spread

# Example: Analyzing a distressed capital structure
V, sigma_V, _ = solve_merton_system(E=1e9, sigma_E=0.80, D=4e9, r=0.045, T=1.0)
print(f"Theoretical Spread: {merton_credit_spread(V, sigma_V, D=4e9, r=0.045, T=1.0):.0f} bps")

```

---

### 📊 Tech Stack

* **Language:** Python 3.10+
* **Math/Stats:** NumPy, SciPy, Pandas
* **Data:** yfinance, FRED API (Planned)

---