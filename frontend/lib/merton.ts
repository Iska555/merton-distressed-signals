/**
 * Merton (1974) structural credit model, client-side.
 *
 * Ported verbatim from the reference solver artifact. Runs entirely in the
 * browser: no backend, no fetch, nothing stored. Every figure on /model and the
 * live half of /mispricing is computed here from inputs visible on screen,
 * which is what lets those pages render with the backend stopped.
 */

/** Normal CDF. Zelen & Severo, A&S 26.2.17, |error| < 7.5e-8. */
export function N(x: number): number {
  if (x < -8) return 0
  if (x > 8) return 1
  const b1 = 0.319381530,
    b2 = -0.356563782,
    b3 = 1.781477937,
    b4 = -1.821255978,
    b5 = 1.330274429,
    p = 0.2316419,
    c = 0.39894228
  const neg = x < 0
  if (neg) x = -x
  const t = 1 / (1 + p * x)
  const v =
    1 - c * Math.exp((-x * x) / 2) * t * (b1 + t * (b2 + t * (b3 + t * (b4 + t * b5))))
  return neg ? 1 - v : v
}

export function d1d2(
  V: number,
  D: number,
  r: number,
  s: number,
  T: number,
): [number, number] {
  const st = s * Math.sqrt(T)
  const a = (Math.log(V / D) + (r + (s * s) / 2) * T) / st
  return [a, a - st]
}

/** Black-Scholes call value: equity as a call on assets, debt face as strike. */
export function callVal(V: number, D: number, r: number, s: number, T: number): number {
  const d = d1d2(V, D, r, s, T)
  return V * N(d[0]) - D * Math.exp(-r * T) * N(d[1])
}

export interface Solution {
  ok: boolean
  V: number
  sV: number
}

/**
 * Recover (V, sigma_V) from observable (E, sigma_E, D, r, T).
 *
 * Nested bisection: an outer search on asset volatility wrapping an inner
 * search on asset value, tolerance 1e-8. Chosen over Newton methods because it
 * cannot diverge -- at extreme leverage with low volatility the system is badly
 * conditioned, and the honest response is to report no solution rather than a
 * number the solver does not believe.
 */
export function solve(
  E: number,
  sE: number,
  D: number,
  r: number,
  T: number,
): Solution {
  function Vfor(sV: number): number {
    let lo = D * 1e-6,
      hi = (E + D) * 40,
      mid = 0
    for (let i = 0; i < 200; i++) {
      mid = (lo + hi) / 2
      if (callVal(mid, D, r, sV, T) < E) lo = mid
      else hi = mid
      if (hi - lo < 1e-10 * Math.max(1, hi)) break
    }
    return mid
  }

  // f(sV) = model-implied equity vol minus target. Increasing in sV.
  function f(sV: number): number {
    const V = Vfor(sV)
    const d = d1d2(V, D, r, sV, T)
    return (sV * V * N(d[0])) / E - sE
  }

  let lo = 1e-4,
    hi = 4.0
  const flo = f(lo),
    fhi = f(hi)
  if (flo > 0 || fhi < 0) return { ok: false, V: NaN, sV: NaN }

  let sV = 0
  for (let i = 0; i < 200; i++) {
    sV = (lo + hi) / 2
    if (f(sV) < 0) lo = sV
    else hi = sV
    if (hi - lo < 1e-9) break
  }
  return { ok: true, V: Vfor(sV), sV }
}

export interface Metrics {
  dd: number
  pd: number
  spread: number
  B: number
}

/**
 * Distance to default, default probability, implied spread and debt value.
 *
 * DD uses the asset drift mu, not r: the physical measure is what a
 * default-probability statement is about. The spread uses r, being a
 * risk-neutral pricing quantity. Conflating the two is a common error.
 */
export function metrics(
  V: number,
  sV: number,
  D: number,
  r: number,
  mu: number,
  T: number,
): Metrics {
  const st = sV * Math.sqrt(T)
  const dd = (Math.log(V / D) + (mu - (sV * sV) / 2) * T) / st
  const d = d1d2(V, D, r, sV, T)
  const inner = N(d[1]) + (V / D) * Math.exp(r * T) * N(-d[0])
  const spread = inner > 0 ? -(1 / T) * Math.log(inner) * 10000 : NaN
  const B = V * N(-d[0]) + D * Math.exp(-r * T) * N(d[1])
  return { dd, pd: N(-dd), spread, B }
}

/** Implied spread at a given leverage D/V, holding volatility and horizon fixed. */
export function spreadAtLev(lev: number, sV: number, r: number, T: number): number {
  const V = 1,
    D = lev
  const d = d1d2(V, D, r, sV, T)
  const inner = N(d[1]) + (V / D) * Math.exp(r * T) * N(-d[0])
  return inner > 0 ? -(1 / T) * Math.log(inner) * 10000 : NaN
}

// ---------------------------------------------------------------- formatting

export function fM(x: number): string {
  if (!isFinite(x)) return 'n/a'
  if (Math.abs(x) >= 10000) return (x / 1000).toFixed(1) + 'bn'
  return Math.round(x).toLocaleString('en-US') + 'm'
}

export function f2(x: number): string {
  return isFinite(x) ? x.toFixed(2) : 'n/a'
}

export function niceTicks(lo: number, hi: number, n: number): number[] {
  const span = hi - lo
  if (!(span > 0)) return [lo]
  const raw = span / n,
    mag = Math.pow(10, Math.floor(Math.log10(raw))),
    norm = raw / mag
  const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag
  const out: number[] = []
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) {
    out.push(+t.toFixed(10))
  }
  return out
}
