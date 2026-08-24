'use client'

import { useMemo, useState } from 'react'
import { metrics, solve } from '@/lib/merton'
import { shadowRating, type RatingTables } from '@/lib/shadowRating'

const S1 = 'var(--series-1)'
const S2 = 'var(--series-2)'

function Field({
  id, label, value, min, max, step, display, onChange,
}: {
  id: string; label: string; value: number; min: number; max: number
  step: number; display: string; onChange: (v: number) => void
}) {
  return (
    <div className="field">
      <div className="field-head">
        <label htmlFor={id}>{label}</label>
        <output htmlFor={id} className="tnum">{display}</output>
      </div>
      <input type="range" id={id} min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(+e.target.value)} />
    </div>
  )
}

export default function MispricingClient({ tables }: { tables: RatingTables }) {
  // Equity side
  const [E, setE] = useState(1800)
  const [sEpct, setSE] = useState(45)
  const [D, setD] = useState(2200)
  const [rPct, setR] = useState(4.3)
  const [T, setT] = useState(3)

  // Accounting side. The benchmark rating sees ONLY these.
  const [ebit, setEbit] = useState(420)
  const [interest, setInterest] = useState(140)
  const [assets, setAssets] = useState(6200)
  const [debt, setDebt] = useState(2200)
  const [ebitda, setEbitda] = useState(680)
  const [revenue, setRevenue] = useState(3400)

  const s = useMemo(() => solve(E, sEpct / 100, D, rPct / 100, T), [E, sEpct, D, rPct, T])
  const m = useMemo(
    () => (s.ok ? metrics(s.V, s.sV, D, rPct / 100, rPct / 100, T) : null),
    [s, D, rPct, T],
  )

  const [forceBand, setForceBand] = useState<'large' | 'small' | null>(null)

  const fundamentals = useMemo(
    () => ({
      ebit: ebit * 1e6,
      interestExpense: interest * 1e6,
      totalAssets: assets * 1e6,
      totalDebt: debt * 1e6,
      ebitda: ebitda * 1e6,
      revenue: revenue * 1e6,
    }),
    [ebit, interest, assets, debt, ebitda, revenue],
  )

  const rating = useMemo(
    () => (tables ? shadowRating(fundamentals, tables, forceBand) : null),
    [tables, fundamentals, forceBand],
  )

  // The counterfactual band, so the page can show what the threshold is worth
  // rather than asserting that it matters.
  const flipped = useMemo(() => {
    if (!tables || !rating?.usable) return null
    const other = rating.sizeBand === 'large' ? 'small' : 'large'
    return shadowRating(fundamentals, tables, other)
  }, [tables, fundamentals, rating])

  const flippedBenchmarkBps =
    flipped?.usable ? tables.benchmarkSpreadBps[flipped.rating] ?? null : null

  const benchmarkBps =
    rating?.usable ? tables.benchmarkSpreadBps[rating.rating] ?? null : null
  const gap = m && benchmarkBps !== null && isFinite(m.spread)
    ? m.spread - benchmarkBps
    : null

  let verdict = '', reading = '', colour = 'var(--ink)'
  if (gap !== null) {
    const mag = Math.abs(gap)
    if (mag < 75) {
      verdict = 'Within noise'
      colour = 'var(--muted)'
      reading =
        'The equity-implied estimate and periodic benchmark broadly agree. Nothing here worth a second look.'
    } else if (gap > 0) {
      verdict = mag > 150 ? 'Equity implies materially more risk' : 'Equity implies more risk'
      colour = S2
      reading =
        'The equity market is pricing more distress than the periodic benchmark. ' +
        'Historically the direction that precedes trouble, and the direction worth ' +
        'investigating. It is a reason to open the filings, not a trade.'
    } else {
      verdict =
        mag > 150 ? 'Periodic benchmark materially wider' : 'Periodic benchmark wider'
      colour = S1
      reading =
        'The periodic benchmark is wider than the equity market implies. This can be ' +
        'a classification or vintage effect rather than evidence about this issuer.'
    }
  }

  return (
    <>
      <section className="section">
        <h2>The two sides, computed separately</h2>
        <p className="prose">
          The left panel drives the equity-implied spread through the Merton solve.
          The right panel drives the benchmark rating through interest coverage and
          scale. <strong>They share no input.</strong> That separation is the whole
          point: the predecessor derived the rating from the model&rsquo;s own asset
          value, so the gap it reported was partly the model arguing with itself.
        </p>

        <div className="gap-panel">
          <div>
            <p className="eyebrow">Equity side · drives implied spread</p>
            <Field id="E" label="Market cap" min={100} max={8000} step={10} value={E}
              display={`$${E.toLocaleString()}m`} onChange={setE} />
            <Field id="sE" label="Equity volatility" min={10} max={150} step={1} value={sEpct}
              display={`${sEpct}%`} onChange={setSE} />
            <Field id="D" label="Debt face value" min={100} max={8000} step={10} value={D}
              display={`$${D.toLocaleString()}m`} onChange={setD} />
            <Field id="r" label="Risk-free rate" min={0} max={10} step={0.05} value={rPct}
              display={`${rPct.toFixed(2)}%`} onChange={setR} />
            <Field id="T" label="Horizon" min={0.5} max={8} step={0.25} value={T}
              display={`${T.toFixed(2)} yr`} onChange={setT} />
          </div>

          <div>
            <p className="eyebrow">Accounting side · drives benchmark rating</p>
            <Field id="ebit" label="EBIT" min={-500} max={2000} step={10} value={ebit}
              display={`$${ebit.toLocaleString()}m`} onChange={setEbit} />
            <Field id="int" label="Interest expense" min={1} max={800} step={5} value={interest}
              display={`$${interest.toLocaleString()}m`} onChange={setInterest} />
            <Field id="ta" label="Total assets" min={200} max={40000} step={100} value={assets}
              display={`$${assets.toLocaleString()}m`} onChange={setAssets} />
            <Field id="td" label="Total debt" min={0} max={20000} step={50} value={debt}
              display={`$${debt.toLocaleString()}m`} onChange={setDebt} />
            <Field id="ebitda" label="EBITDA" min={1} max={4000} step={10} value={ebitda}
              display={`$${ebitda.toLocaleString()}m`} onChange={setEbitda} />
            <Field id="rev" label="Revenue" min={1} max={40000} step={100} value={revenue}
              display={`$${revenue.toLocaleString()}m`} onChange={setRevenue} />
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Divergence</h2>

        <div className="stat-row">
          <div className="stat">
            <div className="v tnum">
              {m && isFinite(m.spread) ? Math.round(m.spread).toLocaleString() : 'n/a'}
            </div>
            <div className="k">Equity-implied spread</div>
            <div className="sub">bps · Merton solve</div>
          </div>
          <div className="stat">
            <div className="v tnum">{rating?.usable ? rating.rating : 'n/a'}</div>
            <div className="k">Shadow rating</div>
            <div className="sub">
              {rating?.usable
                ? `coverage ${isFinite(rating.coverage) ? rating.coverage.toFixed(2) + '×' : '∞'} · ${rating.sizeBand} cap`
                : 'inputs incomplete'}
            </div>
          </div>
          <div className="stat">
            <div className="v tnum">
              {benchmarkBps !== null ? benchmarkBps.toFixed(0) : 'n/a'}
            </div>
            <div className="k">Periodic benchmark</div>
            <div className="sub">
              {rating?.usable ? `${rating.rating} synthetic-rating default spread` : 'n/a'}
            </div>
          </div>
          <div className="stat">
            <div className="v tnum" style={{ color: colour }}>
              {gap === null
                ? 'n/a'
                : (gap >= 0 ? '+' : '−') + Math.abs(Math.round(gap)).toLocaleString()}
            </div>
            <div className="k">Divergence</div>
            <div className="sub">bps · equity less periodic benchmark</div>
          </div>
        </div>

        {gap !== null && (
          <div className="gapline">
            <div className="verdict" style={{ color: colour }}>{verdict}</div>
            <p style={{ fontSize: 13.5, color: 'var(--muted)' }}>{reading}</p>
          </div>
        )}

        {rating?.usable && rating.notch !== 0 && (
          <p className="source-line">
            Rating notched {rating.notch > 0 ? 'down' : 'up'} one grade from{' '}
            {rating.baseRating}: {rating.notchReason}. At most one notch is ever
            applied, and its reason is recorded so the assignment is auditable.
          </p>
        )}

        {rating?.usable && flipped?.usable && (
          <div className="callout callout-neutral">
            <p className="eyebrow">Size-band sensitivity</p>
            <p>
              This firm falls in the <strong>{rating.naturalBand}</strong> band on
              total assets. Rated against the other table it would be{' '}
              <strong>{flipped.rating}</strong> rather than{' '}
              <strong>{rating.rating}</strong>
              {flippedBenchmarkBps !== null && benchmarkBps !== null && (
                <>
                  , moving the benchmark from{' '}
                  <span className="mono tnum">{benchmarkBps.toFixed(0)}</span> to{' '}
                  <span className="mono tnum">{flippedBenchmarkBps.toFixed(0)}</span> bps
                  and the divergence by{' '}
                  <span className="mono tnum">
                    {Math.abs(
                      Math.round(benchmarkBps - flippedBenchmarkBps),
                    ).toLocaleString()}
                  </span>{' '}
                  bps
                </>
              )}
              . Identical fundamentals; only the table changes.
            </p>
            {rating.nearBoundary && (
              <p>
                <strong>This firm sits within 30% of the size boundary.</strong> Its
                rating is partly an artefact of where the cutoff was drawn. About{' '}
                <strong>8.5%</strong> of the filer universe falls in that zone.
              </p>
            )}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
              {(['natural', 'large', 'small'] as const).map((mode) => {
                const active =
                  mode === 'natural' ? forceBand === null : forceBand === mode
                return (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setForceBand(mode === 'natural' ? null : mode)}
                    style={{
                      font: 'inherit',
                      fontSize: 11,
                      fontWeight: 600,
                      letterSpacing: '0.1em',
                      textTransform: 'uppercase',
                      padding: '5px 11px',
                      borderRadius: 999,
                      cursor: 'pointer',
                      border: `1px solid ${active ? 'var(--accent)' : 'var(--rule-sw)'}`,
                      background: active ? 'var(--accent)' : 'transparent',
                      color: active ? 'var(--ground)' : 'var(--muted)',
                    }}
                  >
                    {mode === 'natural' ? 'As classified' : `Force ${mode}`}
                  </button>
                )
              })}
            </div>
            {rating.bandForced && (
              <p style={{ color: 'var(--risk)', fontSize: 13 }}>
                Band is forced. Figures above are a sensitivity, not this
                firm&rsquo;s classification.
              </p>
            )}
          </div>
        )}

        <p className="source-line">
          Benchmark: January 2026 Damodaran synthetic-rating default spread. This
          periodic analytical input is not an ICE index, live credit price or issuer
          bond quote.
        </p>
      </section>

      <section className="section">
        <h2>What was broken, and what is still limited</h2>
        <div className="callout">
          <p className="eyebrow">Read this before using the number</p>
          <p>
            <strong>The circularity, now fixed.</strong> The old pipeline estimated a
            credit rating from Merton asset leverage, then used that rating to look up
            the benchmark spread. Both sides of the comparison descended from the same
            model output. The benchmark rating is now assigned from accounting
            fundamentals alone, meaning interest coverage, scale, profitability and
            debt to earnings, with no Merton quantity anywhere in it. A test asserts that
            the function cannot even accept one.
          </p>
          <p>
            <strong>Levels are not comparable; directions are.</strong> Structural
            models understate observed investment-grade spreads at short horizons,
            because a real spread also pays for liquidity and tax. That is the
            documented credit spread puzzle (Eom, Helwege and Huang 2004; Huang and
            Huang 2012). Read the divergence as a screen for where the equity-implied
            estimate and periodic benchmark disagree and in which direction, not as
            basis points anyone could capture.
          </p>
          <p>
            <strong>The limitation that remains.</strong> The January 2026 Damodaran
            synthetic-rating default spread is a periodic analytical benchmark, not
            this firm&rsquo;s bond, an ICE index or a live credit price. Issuer-level
            pricing needs TRACE, which is not freely available. This divergence is a
            screening direction that tells you where to look, not tradable basis
            points. Calling it an arbitrage signal would claim more than the data can
            carry.
          </p>
          <p>
            <strong>The shadow rating is not an agency rating.</strong> It is
            coverage-driven. A real rating incorporates analyst judgement, management
            access and private information a coverage ratio cannot see.
          </p>
          <p>
            <strong>The two rating tables are nine years apart.</strong> The
            large-firm table is a January 2026 analysis; the small-firm table is
            January 2017. A firm crossing the size boundary is therefore rated against
            thresholds calibrated nearly a decade apart, and the switch is triggered by
            size rather than by date. Both were checked row by row against the
            published source and match exactly, but verification cannot fix a vintage
            gap, only disclose it.
          </p>
          <p>
            <strong>Why the size band uses assets rather than market cap.</strong> The
            published boundary is $5bn of market capitalisation. Market cap is a price,
            and the equity-implied spread on the other side of this comparison is built
            from that same price, so a market-cap band would move both sides together.
            In a distress event equity collapses, the implied spread widens, the firm
            drops a size band, and the benchmark widens too, damping the divergence
            exactly when it should be opening. The bias runs toward{' '}
            <strong>false negatives</strong>, the worst direction for a screen. Total
            assets is price-independent and avoids that coupling.
          </p>
          <p>
            <strong>The substitution is not an equivalence.</strong> $5bn of assets is
            not $5bn of market cap, and the two cannot be reconciled without market caps
            for the whole universe, which the price-API symbol quota forbids. The level
            is a judgement: it sits near the 75th percentile of non-financial filers
            with at least $50M of assets, so it separates roughly the top quartile. The
            matching numeral is a coincidence. The sensitivity control above is the real
            defence, because it lets the choice be measured rather than argued.
          </p>
        </div>
      </section>
    </>
  )
}
