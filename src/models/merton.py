"""
Merton (1974) structural credit model.

Equity is a European call on firm assets, struck at the face value of debt:

    E  = V N(d1) - D e^{-rT} N(d2)
    d1 = [ln(V/D) + (r + sigma_V^2/2) T] / (sigma_V sqrt(T))
    d2 = d1 - sigma_V sqrt(T)

V and sigma_V are unobservable. Three estimators are provided, because the
choice materially moves the answer and therefore belongs in the published
sensitivity analysis rather than in a comment:

  simultaneous  Solve the two coupled equations, pairing the call formula with
                Ito's lemma:  sigma_E = (V/E) N(d1) sigma_V.
                The textbook approach. The second equation is known to be
                unstable for distressed firms.

  iterative     Crosbie & Bohn (2003) / Vassalou & Xing (2004), the approach
                Moody's KMV actually uses. Seed sigma_V, invert the call daily
                to get a V series, recompute sigma_V from V log-returns, repeat
                to convergence. Uses only the call equation, so it avoids the
                unstable one. This is the study default.

  naive         Bharath & Shumway (2008). Closed form, no solving. Shown by
                that paper to forecast default about as well as the full solve,
                which makes it a useful check on whether solver behaviour is
                driving any result.

Nothing here applies sector overrides, floors, or hardcoded substitutions. The
predecessor (backend/signals/generator.py) replaced bank debt with `E * 9.0`
and bank benchmark spreads with constants; those are fabrications and are gone.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq, fsolve
from scipy.stats import norm

__all__ = [
    "MertonSolution",
    "solve_simultaneous",
    "solve_iterative",
    "naive_dd",
    "distance_to_default",
    "default_probability",
    "credit_spread",
    "equity_from_assets",
]

_MIN_SIGMA = 1e-4
_MAX_SIGMA = 5.0


@dataclass
class MertonSolution:
    """Result of a Merton solve, carrying its own diagnostics."""
    V: float
    sigma_V: float
    method: str
    converged: bool
    residual: float = np.nan
    iterations: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def usable(self) -> bool:
        return (
            self.converged
            and np.isfinite(self.V)
            and np.isfinite(self.sigma_V)
            and self.V > 0
            and self.sigma_V > 0
        )


# --------------------------------------------------------------------------
# Core Black-Scholes-Merton relations
# --------------------------------------------------------------------------

def _d1_d2(V: float, D: float, r: float, T: float, sigma_V: float):
    if V <= 0 or D <= 0 or sigma_V <= 0 or T <= 0:
        return np.nan, np.nan
    vol_sqrt_t = sigma_V * np.sqrt(T)
    d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / vol_sqrt_t
    return d1, d1 - vol_sqrt_t


def equity_from_assets(V: float, D: float, r: float, T: float, sigma_V: float) -> float:
    """Value of equity as a call on assets. The one equation everything rests on."""
    d1, d2 = _d1_d2(V, D, r, T, sigma_V)
    if not np.isfinite(d1):
        return np.nan
    return V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)


def distance_to_default(
    V: float, sigma_V: float, D: float, r: float, T: float, *, mu: float | None = None
) -> float:
    """
    Distance to default, in standard deviations of asset value.

        DD = [ln(V/D) + (mu - sigma_V^2/2) T] / (sigma_V sqrt(T))

    `mu` is the expected asset return. Under the risk-neutral measure it is r,
    which is what the credit-spread calculation requires. Empirical KMV work
    often substitutes a realised drift; leaving mu=None uses r, keeping the
    spread and DD mutually consistent.
    """
    if not all(np.isfinite([V, sigma_V, D, r, T])) or V <= 0 or sigma_V <= 0 or D <= 0 or T <= 0:
        return np.nan
    drift = r if mu is None else mu
    return (np.log(V / D) + (drift - 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))


def default_probability(dd: float) -> float:
    """Risk-neutral PD implied by a distance to default: N(-DD).

    This is an *ordinal* risk measure. Structural models are well known to be
    badly calibrated in levels, understating short-horizon PD by an order of
    magnitude. The calibration exhibit on /discrimination demonstrates that on
    this study's own data rather than asserting it.
    """
    return float(norm.cdf(-dd)) if np.isfinite(dd) else np.nan


def credit_spread(dd: float, T: float, recovery_rate: float = 0.40) -> float:
    """
    Merton credit spread in basis points.

        spread = -(1/T) ln(1 - PD * LGD)
    """
    pd_value = default_probability(dd)
    if not np.isfinite(pd_value) or T <= 0:
        return np.nan
    lgd = 1.0 - recovery_rate
    survival = 1.0 - pd_value * lgd
    if survival <= 0:
        return np.inf
    return float(-(1.0 / T) * np.log(survival) * 10_000.0)


# --------------------------------------------------------------------------
# Estimator 1: simultaneous two-equation solve
# --------------------------------------------------------------------------

def solve_simultaneous(
    E: float, sigma_E: float, D: float, r: float, T: float
) -> MertonSolution:
    """
    Solve the call equation and the Ito volatility relation jointly.

    Inputs are scaled to billions before solving. Residuals on raw dollar values
    are numerically hopeless for large firms, which is why the predecessor
    needed a "solver asphyxiation" workaround; scaling is the fix.
    """
    if not all(np.isfinite([E, sigma_E, D, r, T])) or E <= 0 or D <= 0 or sigma_E <= 0:
        return MertonSolution(np.nan, np.nan, "simultaneous", False,
                              notes=("invalid inputs",))

    scale = 1e9
    e_s, d_s = E / scale, D / scale

    def system(params):
        v_s, sigma_v = params
        if v_s <= 0 or sigma_v <= _MIN_SIGMA or sigma_v > _MAX_SIGMA:
            return [1e6, 1e6]
        d1, d2 = _d1_d2(v_s, d_s, r, T, sigma_v)
        if not np.isfinite(d1):
            return [1e6, 1e6]
        model_e = v_s * norm.cdf(d1) - d_s * np.exp(-r * T) * norm.cdf(d2)
        model_sigma_e = (v_s / e_s) * norm.cdf(d1) * sigma_v
        return [model_e - e_s, model_sigma_e - sigma_E]

    # Deterministic guess ladder, ordered from the most to the least typical.
    guesses = [
        (e_s + d_s, sigma_E * e_s / (e_s + d_s)),
        (e_s + d_s, 0.25),
        (e_s + 0.8 * d_s, 0.40),
        (e_s + 0.5 * d_s, max(sigma_E * 0.5, 0.05)),
    ]

    best: MertonSolution | None = None
    for guess in guesses:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                sol, info, status, _ = fsolve(system, guess, full_output=True)
            except Exception:  # noqa: BLE001 - solver blow-up is a valid outcome
                continue
        v_s, sigma_v = sol
        residual = float(np.max(np.abs(info["fvec"])))
        if v_s > 0 and _MIN_SIGMA < sigma_v < _MAX_SIGMA:
            candidate = MertonSolution(
                V=float(v_s * scale), sigma_V=float(sigma_v),
                method="simultaneous", converged=(status == 1 and residual < 1e-6),
                residual=residual,
            )
            if candidate.converged:
                return candidate
            if best is None or residual < best.residual:
                best = candidate

    if best is not None:
        return best
    return MertonSolution(np.nan, np.nan, "simultaneous", False,
                          notes=("no convergence from any start",))


# --------------------------------------------------------------------------
# Estimator 2: KMV iterative procedure (study default)
# --------------------------------------------------------------------------

def _invert_call(E: float, D: float, r: float, T: float, sigma_V: float) -> float:
    """
    Recover V from observed equity, given sigma_V, by inverting the call.

    Monotone in V, so a bracketed root-find is both safe and deterministic --
    no starting-point sensitivity, unlike the simultaneous solve.
    """
    if E <= 0 or D <= 0 or sigma_V <= 0:
        return np.nan

    def objective(v):
        return equity_from_assets(v, D, r, T, sigma_V) - E

    lo = E + D * np.exp(-r * T) * 1e-6
    hi = (E + D) * 10.0
    try:
        f_lo, f_hi = objective(lo), objective(hi)
        tries = 0
        while f_lo > 0 and tries < 60:
            lo *= 0.5
            f_lo = objective(lo)
            tries += 1
        while f_hi < 0 and tries < 120:
            hi *= 2.0
            f_hi = objective(hi)
            tries += 1
        if f_lo > 0 or f_hi < 0:
            return np.nan
        return float(brentq(objective, lo, hi, xtol=1e-8, rtol=1e-10, maxiter=200))
    except Exception:  # noqa: BLE001
        return np.nan


def solve_iterative(
    equity_series: np.ndarray,
    D: float,
    r: float,
    T: float,
    *,
    trading_days: int = 252,
    tol: float = 1e-4,
    max_iter: int = 60,
) -> MertonSolution:
    """
    Crosbie & Bohn (2003) iterative estimator -- the KMV procedure.

    Args:
        equity_series: daily market capitalisation, chronological, length >= 30.
                       The LAST element is the observation date.
        D:             default barrier (face value of debt at the chosen convention)
        r:             risk-free rate, annualised decimal
        T:             horizon in years

    The loop uses only the call equation, avoiding the unstable Ito relation.
    It converges when successive sigma_V estimates differ by less than `tol`.
    """
    equity_series = np.asarray(equity_series, dtype=float)
    equity_series = equity_series[np.isfinite(equity_series) & (equity_series > 0)]

    if equity_series.size < 30 or D <= 0 or not np.isfinite(D):
        return MertonSolution(np.nan, np.nan, "iterative", False,
                              notes=("insufficient equity history",))

    E_last = float(equity_series[-1])

    # Seed with the standard leverage-scaled equity volatility.
    equity_returns = np.diff(np.log(equity_series))
    sigma_E = float(np.std(equity_returns, ddof=1) * np.sqrt(trading_days))
    if not np.isfinite(sigma_E) or sigma_E <= 0:
        return MertonSolution(np.nan, np.nan, "iterative", False,
                              notes=("degenerate equity volatility",))
    sigma_V = max(sigma_E * E_last / (E_last + D), _MIN_SIGMA)

    for iteration in range(1, max_iter + 1):
        asset_values = np.array(
            [_invert_call(e, D, r, T, sigma_V) for e in equity_series]
        )
        if not np.all(np.isfinite(asset_values)) or np.any(asset_values <= 0):
            return MertonSolution(np.nan, np.nan, "iterative", False,
                                  iterations=iteration,
                                  notes=("call inversion failed",))

        asset_returns = np.diff(np.log(asset_values))
        sigma_V_new = float(np.std(asset_returns, ddof=1) * np.sqrt(trading_days))
        sigma_V_new = float(np.clip(sigma_V_new, _MIN_SIGMA, _MAX_SIGMA))

        if abs(sigma_V_new - sigma_V) < tol:
            # Re-invert at the FINAL sigma_V so the returned pair satisfies the
            # call equation exactly. `asset_values` was computed with the
            # previous iterate; returning it alongside sigma_V_new would hand
            # downstream DD a mutually inconsistent (V, sigma_V).
            V = _invert_call(E_last, D, r, T, sigma_V_new)
            if not np.isfinite(V) or V <= 0:
                return MertonSolution(np.nan, np.nan, "iterative", False,
                                      iterations=iteration,
                                      notes=("final inversion failed",))
            return MertonSolution(
                V=float(V), sigma_V=sigma_V_new, method="iterative", converged=True,
                residual=abs(sigma_V_new - sigma_V), iterations=iteration,
            )
        sigma_V = sigma_V_new

    V = _invert_call(E_last, D, r, T, sigma_V)
    return MertonSolution(
        V=float(V), sigma_V=float(sigma_V), method="iterative", converged=False,
        residual=np.nan, iterations=max_iter, notes=("hit iteration cap",),
    )


# --------------------------------------------------------------------------
# Estimator 3: Bharath & Shumway (2008) naive
# --------------------------------------------------------------------------

def naive_dd(
    E: float, sigma_E: float, D: float, r_annual_return: float, T: float = 1.0
) -> MertonSolution:
    """
    Closed-form naive estimator, Bharath & Shumway (2008) eq. 12-14.

        naive sigma_D = 0.05 + 0.25 * sigma_E
        naive sigma_V = (E sigma_E + D * naive sigma_D) / (E + D)
        naive V       = E + D
        naive mu      = prior year's equity return

    No solving, so it cannot fail to converge. If a headline result holds under
    the full solve but vanishes here (or vice versa), that is diagnostic of
    solver artefacts rather than economics.
    """
    if not all(np.isfinite([E, sigma_E, D, T])) or E <= 0 or D <= 0 or sigma_E <= 0:
        return MertonSolution(np.nan, np.nan, "naive", False, notes=("invalid inputs",))

    sigma_debt = 0.05 + 0.25 * sigma_E
    sigma_V = (E * sigma_E + D * sigma_debt) / (E + D)
    V = E + D
    return MertonSolution(V=float(V), sigma_V=float(sigma_V), method="naive",
                          converged=True, residual=0.0, iterations=0)
