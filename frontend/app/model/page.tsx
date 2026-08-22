'use client'

import { useMemo, useState } from 'react'
import LineChart from '@/components/LineChart'
import { callVal, f2, fM, metrics, solve, spreadAtLev } from '@/lib/merton'

const S1 = 'var(--series-1)'
const S2 = 'var(--series-2)'

function Slider({
  id,
  label,
  min,
  max,
  step,
  value,
  display,
  onChange,
}: {
  id: string
  label: string
  min: number
  max: number
  step: number
  value: number
  display: string
  onChange: (v: number) => void
}) {
  return (
    <div className="field">
      <div className="field-head">
        <label htmlFor={id}>{label}</label>
        <output htmlFor={id} className="tnum">
          {display}
        </output>
      </div>
      <input
        type="range"
        id={id}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(+e.target.value)}
      />
    </div>
  )
}

export default function ModelPage() {
  const [E, setE] = useState(800)
  const [sEpct, setSE] = useState(60)
  const [D, setD] = useState(2400)
  const [rPct, setR] = useState(4.3)
  const [T, setT] = useState(3)
  const [muPct, setMu] = useState(4.3)

  const sE = sEpct / 100,
    r = rPct / 100,
    mu = muPct / 100

  const s = useMemo(() => solve(E, sE, D, r, T), [E, sE, D, r, T])
  const m = useMemo(
    () => (s.ok ? metrics(s.V, s.sV, D, r, mu, T) : null),
    [s, D, r, mu, T],
  )

  const chart1 = useMemo(() => {
    if (!s.ok) return null
    const xmax = Math.max(D * 2.2, s.V * 1.5)
    const payoff: [number, number][] = []
    const today: [number, number][] = []
    for (let i = 0; i <= 180; i++) {
      const v = (xmax * i) / 180
      payoff.push([v, Math.max(v - D, 0)])
      today.push([v, v <= 0 ? 0 : callVal(v, D, r, s.sV, T)])
    }
    const ymax = Math.max(xmax - D, callVal(xmax, D, r, s.sV, T)) * 1.05
    return { xmax, payoff, today, ymax }
  }, [s, D, r, T])

  const chart2 = useMemo(() => {
    if (!s.ok || !m) return null
    const lo = 0.05,
      hi = 0.98
    const pts: [number, number][] = []
    for (let j = 0; j <= 180; j++) {
      const lv = lo + ((hi - lo) * j) / 180
      pts.push([lv, spreadAtLev(lv, s.sV, r, T)])
    }
    const finite = pts.map((p) => p[1]).filter(isFinite)
    const ymax = Math.max(
      300,
      Math.min(
        Math.max(...finite) * 1.05,
        Math.max(1200, (isFinite(m.spread) ? m.spread : 0) * 1.8),
      ),
    )
    return { lo, hi, pts, ymax }
  }, [s, m, r, T])

  return (
    <div className="wrap">
      <header className="masthead">
        <p className="eyebrow">The model · Merton (1974)</p>
        <h1>Equity is a call option on the firm&rsquo;s assets.</h1>
        <p className="lede">
          Everything below follows from that one idea. Shareholders own the upside
          above the debt and can walk away below it, so the same mathematics that
          prices an option prices the firm&rsquo;s credit risk. Move the inputs and
          watch it work.
        </p>
      </header>

      <section className="section">
        <h2>Solve it</h2>
        <p className="prose">
          Asset value and asset volatility are not observable. Two equations recover
          them from things that are: market capitalisation and equity volatility. The
          solve runs in your browser, live, on every change.
        </p>

        <div className="solver">
          <div className="inputs">
            <Slider id="E" label="Market cap" min={50} max={8000} step={10} value={E}
              display={'$' + fM(E)} onChange={setE} />
            <Slider id="sE" label="Equity volatility" min={10} max={180} step={1} value={sEpct}
              display={sEpct.toFixed(0) + '%'} onChange={setSE} />
            <Slider id="D" label="Debt face value" min={50} max={8000} step={10} value={D}
              display={'$' + fM(D)} onChange={setD} />
            <Slider id="r" label="Risk-free rate" min={0} max={10} step={0.05} value={rPct}
              display={rPct.toFixed(2) + '%'} onChange={setR} />
            <Slider id="T" label="Horizon" min={0.25} max={8} step={0.25} value={T}
              display={T.toFixed(2) + ' yr'} onChange={setT} />
            <Slider id="mu" label="Asset drift" min={-15} max={20} step={0.5} value={muPct}
              display={muPct.toFixed(1) + '%'} onChange={setMu} />
          </div>

          <div className="outputs">
            <div className="out-grid">
              <div className="out">
                <div className="v tnum">{s.ok ? '$' + fM(s.V) : 'n/a'}</div>
                <div className="k">Asset value</div>
                <div className="sub">{s.ok ? `leverage D/V ${(D / s.V).toFixed(2)}` : ''}</div>
              </div>
              <div className="out">
                <div className="v tnum">{s.ok ? (s.sV * 100).toFixed(1) + '%' : 'n/a'}</div>
                <div className="k">Asset volatility</div>
                <div className="sub">deleveraged</div>
              </div>
              <div className="out">
                <div className="v tnum">{m ? f2(m.dd) + 'σ' : 'n/a'}</div>
                <div className="k">Distance to default</div>
                <div className="sub">std devs to the barrier</div>
              </div>
            </div>
            <div className="out-grid" style={{ borderBottom: 'none' }}>
              <div className="out">
                <div className="v tnum">
                  {m
                    ? (m.pd * 100 < 0.01 && m.pd > 0 ? '<0.01' : (m.pd * 100).toFixed(2)) + '%'
                    : 'n/a'}
                </div>
                <div className="k">Default probability</div>
                <div className="sub">{m ? `over ${T.toFixed(2)} years` : ''}</div>
              </div>
              <div className="out">
                <div className="v tnum">
                  {m && isFinite(m.spread) ? Math.round(m.spread).toLocaleString('en-US') : 'n/a'}
                </div>
                <div className="k">Implied credit spread</div>
                <div className="sub">basis points over risk-free</div>
              </div>
              <div className="out">
                <div className="v tnum">{m ? '$' + fM(m.B) : 'n/a'}</div>
                <div className="k">Debt value</div>
                <div className="sub">present value of the claim</div>
              </div>
            </div>
            <div className="solve-note">
              <span
                className="dot"
                style={{ background: s.ok ? S1 : 'var(--risk)' }}
                aria-hidden
              />
              <span style={{ color: s.ok ? 'var(--muted)' : 'var(--risk)' }}>
                {s.ok
                  ? `Converged. Asset volatility ${(s.sV * 100).toFixed(1)}% is the deleveraged equity volatility of ${sEpct.toFixed(0)}%.`
                  : 'No solution in the search bracket. The equations are badly conditioned at these inputs, usually very low equity volatility with very high leverage.'}
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>What the solve is doing</h2>
        <div className="charts">
          <div className="chartbox">
            <p className="chart-title">Equity as a call option</p>
            <p className="chart-sub">Equity value against asset value. Debt face is the strike.</p>
            {chart1 && s.ok && (
              <LineChart
                ariaLabel="Equity value against asset value, showing the call option payoff and its value today"
                xDomain={[0, chart1.xmax]}
                yDomain={[0, chart1.ymax]}
                xFmt={(t) => '$' + (t >= 1000 ? (t / 1000).toFixed(1) + 'bn' : Math.round(t) + 'm')}
                yFmt={(t) => (t >= 1000 ? (t / 1000).toFixed(1) + 'bn' : Math.round(t) + 'm')}
                xLabel="Asset value V"
                yLabel="Equity value"
                series={[
                  { pts: chart1.payoff, color: S2, dash: '5 4' },
                  { pts: chart1.today, color: S1 },
                ]}
                marker={{ x: s.V, y: E, color: S1, label: 'this firm' }}
                tip={(xv) => {
                  if (xv < 0 || xv > chart1.xmax) return ''
                  const today = xv <= 0 ? 0 : callVal(xv, D, r, s.sV, T)
                  return `<b>V &nbsp;$${fM(xv)}</b><br>value today &nbsp;$${fM(today)}<br>at maturity &nbsp;$${fM(Math.max(xv - D, 0))}`
                }}
              />
            )}
            <div className="legend">
              <span><span className="dot" style={{ background: S1 }} />Value today</span>
              <span><span className="dot" style={{ background: S2 }} />Payoff at maturity</span>
            </div>
          </div>

          <div className="chartbox">
            <p className="chart-title">Implied spread against leverage</p>
            <p className="chart-sub">Holding asset volatility and horizon fixed. Note the convexity.</p>
            {chart2 && s.ok && m && (
              <LineChart
                ariaLabel="Implied credit spread against leverage, with the current firm marked"
                xDomain={[chart2.lo, chart2.hi]}
                yDomain={[0, chart2.ymax]}
                xFmt={(t) => t.toFixed(2)}
                yFmt={(t) => Math.round(t).toLocaleString('en-US')}
                xLabel="Leverage D / V"
                yLabel="Implied spread (bps)"
                series={[{ pts: chart2.pts, color: S1 }]}
                marker={{
                  x: Math.min(D / s.V, chart2.hi),
                  y: m.spread,
                  color: S1,
                  label: 'this firm',
                }}
                tip={(xv) => {
                  if (xv < chart2.lo || xv > chart2.hi) return ''
                  const sp = spreadAtLev(xv, s.sV, r, T)
                  return `<b>leverage &nbsp;${xv.toFixed(2)}</b><br>spread &nbsp;${isFinite(sp) ? Math.round(sp).toLocaleString('en-US') : 'n/a'} bps`
                }}
              />
            )}
            <div className="legend">
              <span><span className="dot" style={{ background: S1 }} />Implied spread · current firm marked</span>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Where it breaks</h2>
        <details className="spec">
          <summary>Assumptions, and the firms they fail on</summary>
          <div className="spec-body">
            <p>
              <strong>The two equations being solved.</strong> The first prices equity as
              a European call on assets. The second links the two volatilities through the
              option&rsquo;s delta.
            </p>
            <div className="eq">
              E = V·N(d₁) − D·e<sup>−rT</sup>·N(d₂)
              <br />
              σ<sub>E</sub>·E = σ<sub>V</sub>·V·N(d₁)
            </div>
            <ul>
              <li>
                <strong>Constant volatility.</strong> Asset volatility jumps precisely when
                it matters most, which is when a firm is failing. The model will be slowest
                exactly at the moment you need it fastest.
              </li>
              <li>
                <strong>One zero-coupon bond.</strong> Real capital structures have maturity
                ladders, covenants, seniority and secured claims. Collapsing them to a single
                face value is a large simplification.
              </li>
              <li>
                <strong>Default only at maturity.</strong> Firms breach covenants and run out
                of cash between dates. Barrier variants address this; this one does not.
              </li>
              <li>
                <strong>Banks are not Merton objects.</strong> Deposit funding, opacity and
                off-balance-sheet exposure break the asset-value story. Silicon Valley Bank
                and Credit Suisse were liquidity runs, not asset insolvencies, which is why
                they sit in a separate illustrative section of this study rather than in the
                sample.
              </li>
              <li>
                <strong>Neither are partnerships or trusts.</strong> A limited partnership
                interest is not a call option on assets. These are excluded on modelling
                grounds, not data grounds.
              </li>
              <li>
                <strong>Short-horizon spreads come out too low.</strong> At one-year horizons
                the model produces spreads far below what investment-grade bonds actually
                trade at. This is the documented credit spread puzzle (Eom, Helwege and Huang
                2004; Huang and Huang 2012): much of an observed spread is liquidity and tax,
                not default risk. It is the main reason the divergence measure is read as
                direction and change rather than as a level.
              </li>
              <li>
                <strong>Fraud is invisible.</strong> The model reads the balance sheet it is
                given. If the balance sheet is false, so is the output.
              </li>
            </ul>
            <p>
              <strong>Numerical note.</strong> The solve here is nested bisection: an outer
              search on asset volatility wrapping an inner search on asset value, tolerance
              1e-8. At extreme leverage with low volatility the equations become badly
              conditioned and the panel above says so rather than reporting a number it does
              not believe.
            </p>
          </div>
        </details>
      </section>

      <section className="section">
        <p className="source-line">
          Every figure on this page is computed in your browser from the inputs shown.
          Nothing is fetched, nothing is stored, and no figure here is an empirical result
          about any real company.
        </p>
      </section>
    </div>
  )
}
