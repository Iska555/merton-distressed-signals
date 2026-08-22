import Link from 'next/link'
import { getManifest, getMeasurement, pct } from '@/lib/siteData'

function Bar({ rate }: { rate: number }) {
  return (
    <div
      aria-hidden
      style={{
        height: 6,
        background: 'var(--grid)',
        position: 'relative',
        minWidth: 60,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          width: `${Math.max(0, Math.min(1, rate)) * 100}%`,
          background: 'var(--series-1)',
        }}
      />
    </div>
  )
}

export default function MeasurementPage() {
  const m = getMeasurement()
  const manifest = getManifest()

  if (!m) {
    return (
      <div className="wrap">
        <header className="masthead">
          <p className="eyebrow">Measurement</p>
          <h1>Not yet computed.</h1>
          <p className="lede">
            The audit output is absent from <span className="mono">data/processed/</span>.
            Run <span className="mono">python -m scripts.audit_resolution</span> then{' '}
            <span className="mono">python -m scripts.build_site_data</span>.
          </p>
        </header>
      </div>
    )
  }

  const unavailable = m.exclusion_families['data_unavailability'] ?? 0
  const inapplicable = m.exclusion_families['model_inapplicability'] ?? 0

  return (
    <div className="wrap">
      <header className="masthead">
        <p className="eyebrow">Measurement</p>
        <h1>
          Most defaulted firms cannot be studied at all, and which ones is not
          random.
        </h1>
        <p className="lede">
          Of {m.total_candidates} bankruptcy filings sampled from{' '}
          {m.window.sampled_from}–{m.window.sampled_to}, {m.resolved} could be
          resolved to a ticker whose price history is actually retrievable. The
          survivors are systematically larger, later, and less financial than the
          population they came from.
        </p>
      </header>

      <section className="section">
        <h2>Two structural thresholds, not one</h2>
        <p className="prose">
          A firm&rsquo;s ticker has to be recovered from its own filings, because
          every register of current tickers has already forgotten it. Two changes
          in SEC filing rules govern whether that is possible at all.
        </p>

        <div className="stat-row">
          <div className="stat">
            <div className="v tnum">~2011</div>
            <div className="k">XBRL instances begin</div>
            <div className="sub">before this, no machine-readable filing data</div>
          </div>
          <div className="stat">
            <div className="v tnum">2019</div>
            <div className="k">Cover-page trading symbol</div>
            <div className="sub">FAST Act Modernization rule</div>
          </div>
        </div>

        <div className="callout callout-neutral">
          <p className="eyebrow">Verified directly</p>
          <p>
            Kodak&rsquo;s 2011 10-K cover page carries only{' '}
            <em>&ldquo;Title of each Class&rdquo;</em> and{' '}
            <em>&ldquo;Name of each exchange on which registered&rdquo;</em>. There
            is <strong>no trading symbol on the page at all</strong> — the column
            was created by the 2019 rule. Cover-page extraction, the obvious
            fallback for older filings, is therefore not merely unreliable before
            2019: the datum does not exist.
          </p>
          <p>
            What survives is Item 5 prose, which states the symbol in a sentence:{' '}
            <em>&ldquo;traded on the New York Stock Exchange under the symbol
            EK&rdquo;</em>. That is the second provenance tier, and it carries much
            of the pre-2019 sample.
          </p>
        </div>
      </section>

      <section className="section">
        <h2>The era gradient</h2>
        <p className="prose">
          Resolution rises steeply across the window. This is the single most
          consequential fact about the sample: the treatment cohort piles up in
          the most recent years, which is a specific and unusual credit regime
          rather than a neutral period.
        </p>

        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr>
                <th>Era</th>
                <th style={{ textAlign: 'right' }}>Candidates</th>
                <th style={{ textAlign: 'right' }}>Resolved</th>
                <th style={{ textAlign: 'right' }}>Rate</th>
                <th style={{ width: 160 }}>&nbsp;</th>
                <th style={{ textAlign: 'right' }}>via XBRL</th>
                <th style={{ textAlign: 'right' }}>via text</th>
              </tr>
            </thead>
            <tbody>
              {m.by_era.map((e) => (
                <tr key={e.label}>
                  <td className="mono">{e.label}</td>
                  <td className="num">{e.n}</td>
                  <td className="num">{e.resolved}</td>
                  <td className="num">{pct(e.rate, 0)}</td>
                  <td><Bar rate={e.rate} /></td>
                  <td className="num">{e.via_xbrl}</td>
                  <td className="num">{e.via_text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="callout">
          <p className="eyebrow">Why this bounds the claim</p>
          <p>
            A sample concentrated in 2022–24 is a sample of the fastest tightening
            cycle in forty years, the March 2023 regional bank failures, and a
            concentrated wave of rate-sensitive bankruptcies. The earlier window is
            a near-zero-rate era with historically suppressed default rates.{' '}
            <strong>Discriminatory power measured on one does not transfer to the
            other</strong>, so every headline metric is reported stratified by era
            rather than pooled. If the strata disagree, that is the result.
          </p>
        </div>
      </section>

      <section className="section">
        <h2>Size — no measurable gradient</h2>
        <p className="prose">
          Among firms reporting a public float there is <strong>no monotone
          trend</strong>. The only real gap is for registrants reporting no float
          at all — shells, liquidating trusts and partnerships — which is a
          filer-type effect rather than a size one, and those are excluded on
          modelling grounds regardless.
        </p>
        <div className="callout callout-neutral">
          <p className="eyebrow">Corrected</p>
          <p>
            An earlier run of this audit, on 190 candidates, reported that float
            ≥ $200M resolved at 79% against 51% below, and concluded the cohort
            skewed large. At 346 candidates that ordering does not hold and the
            trend disappears. It was small-sample noise at roughly ten to twenty-five
            observations per cell. Cross-tabs on this page are now published only
            with their cell counts beside them.
          </p>
        </div>
        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr>
                <th>Public float at last 10-K</th>
                <th style={{ textAlign: 'right' }}>Candidates</th>
                <th style={{ textAlign: 'right' }}>Resolved</th>
                <th style={{ textAlign: 'right' }}>Rate</th>
                <th style={{ width: 160 }}>&nbsp;</th>
              </tr>
            </thead>
            <tbody>
              {m.by_size.map((b) => (
                <tr key={b.label}>
                  <td className="mono">{b.label}</td>
                  <td className="num">{b.n}</td>
                  <td className="num">{b.resolved}</td>
                  <td className="num">{pct(b.rate, 0)}</td>
                  <td><Bar rate={b.rate} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>The sector gradient</h2>
        <p className="prose">
          Financials resolve poorly and are a large share of candidates. The cohort
          therefore under-samples exactly the sector where the Merton model is
          least applicable — which flatters the headline result and weakens the
          sector panel. Both directions are stated rather than only the convenient
          one.
        </p>
        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr>
                <th>SIC division</th>
                <th style={{ textAlign: 'right' }}>Candidates</th>
                <th style={{ textAlign: 'right' }}>Resolved</th>
                <th style={{ textAlign: 'right' }}>Rate</th>
                <th style={{ width: 160 }}>&nbsp;</th>
              </tr>
            </thead>
            <tbody>
              {m.by_sector.map((s) => (
                <tr key={s.sector}>
                  <td>{s.sector}</td>
                  <td className="num">{s.n}</td>
                  <td className="num">{s.resolved}</td>
                  <td className="num">{pct(s.rate, 0)}</td>
                  <td><Bar rate={s.rate} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>Why each excluded firm was excluded</h2>
        <p className="prose">
          Two families, never pooled, because they have opposite implications.
          <strong> Data unavailability</strong> means the firm belongs in the study
          and the sources cannot support it — a limitation, and possibly a biased
          one. <strong>Model inapplicability</strong> means the sources are fine and
          the firm is not a Merton object — a scope definition, and a correct
          exclusion.
        </p>

        <div className="stat-row">
          <div className="stat">
            <div className="v tnum">{unavailable}</div>
            <div className="k">Data unavailability</div>
            <div className="sub">a limitation</div>
          </div>
          <div className="stat">
            <div className="v tnum">{inapplicable}</div>
            <div className="k">Model inapplicability</div>
            <div className="sub">a scope definition</div>
          </div>
          <div className="stat">
            <div className="v tnum">{m.chapter_22_count}</div>
            <div className="k">Chapter 22</div>
            <div className="sub">filed bankruptcy more than once</div>
          </div>
        </div>

        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr>
                <th>Reason code</th>
                <th>Family</th>
                <th style={{ textAlign: 'right' }}>N</th>
                <th style={{ textAlign: 'right' }}>Share</th>
              </tr>
            </thead>
            <tbody>
              {m.reason_codes.map((r) => (
                <tr key={r.code}>
                  <td className="mono">{r.code}</td>
                  <td style={{ color: 'var(--muted)', fontSize: 12 }}>
                    {r.family.replace(/_/g, ' ')}
                  </td>
                  <td className="num">{r.n}</td>
                  <td className="num">{pct(r.share, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>Two traps that would have poisoned the study silently</h2>

        <div className="callout">
          <p className="eyebrow">The spliced ticker</p>
          <p>
            Bed Bath &amp; Beyond traded near <strong>$0.07</strong> before its
            April 2023 filing. A major free price source returns a continuous
            &ldquo;BBBY&rdquo; series showing <strong>$19–36 and rising</strong>{' '}
            straight through the bankruptcy — those are Overstock/Beyond Inc.
            prices, retro-mapped onto the recycled ticker. A pipeline trusting it
            would compute a healthy firm through a bankruptcy and record it as a
            model failure. Every series is therefore validated against the
            symbol&rsquo;s own trading window before use, and rejected rather than
            repaired.
          </p>
        </div>

        <div className="callout">
          <p className="eyebrow">The concurrent symbol</p>
          <p>
            A registrant cannot trade under two symbols at once, so two candidate
            symbols whose trading windows <em>overlap</em> cannot both belong to
            it. A genuine re-ticker shows a handoff instead: Walter
            Investment&rsquo;s WAC ends 2018-02-09 as Ditech&rsquo;s DHCP begins
            2018-02-06. Overlapping candidates are flagged and{' '}
            <strong>never auto-ranked</strong>, because the data does not say which
            is right and ranking would silently choose one.
          </p>
        </div>
      </section>

      <section className="section">
        <p className="source-line">
          Source: SEC EDGAR full-text search (8-K Item 1.03) and XBRL company
          facts; symbol windows from the price vendor&rsquo;s public listing file.{' '}
          {manifest
            ? `Generated ${manifest.generated_utc.slice(0, 10)} at commit ${manifest.git_commit} from data/processed/resolution_audit.csv.`
            : ''}{' '}
          Sample construction and full limitations on <Link href="/data">Data</Link>.
        </p>
      </section>
    </div>
  )
}
