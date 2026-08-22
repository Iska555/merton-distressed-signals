import fs from 'node:fs'
import path from 'node:path'
import Link from 'next/link'
import { getManifest, getMeasurement, pct } from '@/lib/siteData'

interface Corroboration {
  rows: {
    grade: string
    fred_bps: number
    damodaran_bps: number
    difference_bps: number
    ratio: number | null
  }[]
  fred_observation: string
  damodaran_vintage: string
  note: string
}

function readCorroboration(): Corroboration | null {
  try {
    return JSON.parse(
      fs.readFileSync(
        path.join(process.cwd(), 'public', 'data', 'spread_corroboration.json'),
        'utf-8',
      ),
    ) as Corroboration
  } catch {
    return null
  }
}

export default function DataPage() {
  const manifest = getManifest()
  const m = getMeasurement()
  const corr = readCorroboration()

  return (
    <div className="wrap">
      <header className="masthead">
        <p className="eyebrow">Data</p>
        <h1>Sources, sample construction, and what the study cannot claim.</h1>
        <p className="lede">
          Every figure on this site traces to a file listed here or to a computation
          from inputs shown on screen. Where a number could not be sourced, the page
          carrying it says so rather than filling the gap.
        </p>
      </header>

      <section className="section">
        <h2>Sources</h2>
        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr>
                <th>Source</th>
                <th>Used for</th>
                <th>Identifier</th>
                <th>Access</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>SEC EDGAR full-text search</td>
                <td>Bankruptcy events</td>
                <td className="mono">8-K Item 1.03</td>
                <td>Public, no key. Covers 2001 onward</td>
              </tr>
              <tr>
                <td>SEC XBRL company facts</td>
                <td>Debt, share counts, public float, trading symbol</td>
                <td className="mono">data.sec.gov/api/xbrl</td>
                <td>Public, no key</td>
              </tr>
              <tr>
                <td>SEC DERA Financial Statement Data Sets</td>
                <td>Point-in-time filer universe and bulk fundamentals</td>
                <td className="mono">quarterly ZIP</td>
                <td>Public, no key</td>
              </tr>
              <tr>
                <td>FRED ICE BofA OAS indices</td>
                <td>Cohort benchmark spreads</td>
                <td className="mono">BAMLC0A1CAAA … BAMLH0A3HYC</td>
                <td>API key, fetched at build time only</td>
              </tr>
              <tr>
                <td>Price vendor listing file</td>
                <td>Symbol trading windows, delisting dates</td>
                <td className="mono">supported_tickers</td>
                <td>Public file, no key</td>
              </tr>
            </tbody>
          </table>
        </div>
        {manifest && (
          <p className="source-line">
            Site data generated {manifest.generated_utc.slice(0, 10)} at commit{' '}
            <span className="mono">{manifest.git_commit}</span>.
          </p>
        )}
      </section>

      <section className="section">
        <h2>Committed outputs</h2>
        {manifest ? (
          <div className="scroll-x">
            <table className="data">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Built from</th>
                  <th style={{ textAlign: 'right' }}>Rows in</th>
                  <th>Contents</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(manifest.files).map(([name, meta]) => (
                  <tr key={name}>
                    <td className="mono">{name}</td>
                    <td className="mono" style={{ fontSize: 12 }}>{meta.source}</td>
                    <td className="num">{meta.rows_in}</td>
                    <td style={{ fontSize: 12.5, color: 'var(--muted)' }}>
                      {meta.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="prose">No manifest found. Run <span className="mono">python -m scripts.build_site_data</span>.</p>
        )}
      </section>

      {corr && (
        <section className="section">
          <h2>Validation: two unrelated sources agree on units</h2>
          <p className="prose">
            A factor-of-100 error in a percent-to-basis-point conversion is easy to
            make and invisible once made, because the resulting numbers still look
            like spreads. This checks the FRED figures against Damodaran&rsquo;s
            synthetic-rating spread column, which is built from traded bonds and has
            no connection to FRED.
          </p>
          <div className="scroll-x">
            <table className="data">
              <thead>
                <tr>
                  <th>Grade</th>
                  <th style={{ textAlign: 'right' }}>FRED ({corr.fred_observation})</th>
                  <th style={{ textAlign: 'right' }}>
                    Damodaran ({corr.damodaran_vintage})
                  </th>
                  <th style={{ textAlign: 'right' }}>Difference</th>
                </tr>
              </thead>
              <tbody>
                {corr.rows.map((r) => (
                  <tr key={r.grade}>
                    <td className="mono">{r.grade}</td>
                    <td className="num">{r.fred_bps.toFixed(0)}</td>
                    <td className="num">{r.damodaran_bps}</td>
                    <td
                      className="num"
                      style={{
                        color:
                          Math.abs(r.difference_bps) > 100 ? 'var(--muted)' : 'inherit',
                      }}
                    >
                      {r.difference_bps > 0 ? '+' : ''}
                      {r.difference_bps.toFixed(0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="prose">
            Investment grade agrees within a few basis points across two independent
            sources, which is strong evidence the conversion is correct. {corr.note}
          </p>
        </section>
      )}

      <section className="section">
        <h2>Exclusions, split by cause</h2>
        <p className="prose">
          Two families with opposite implications, reported separately and never
          pooled. A single undifferentiated exclusion count would hide the
          distinction.
        </p>
        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr>
                <th>Family</th>
                <th>Meaning</th>
                <th>Implication</th>
                <th style={{ textAlign: 'right' }}>N</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="mono">data_unavailability</td>
                <td>The firm belongs in the study; the sources cannot support it</td>
                <td>A limitation, possibly a biased one</td>
                <td className="num">{m?.exclusion_families['data_unavailability'] ?? '—'}</td>
              </tr>
              <tr>
                <td className="mono">model_inapplicability</td>
                <td>The sources are fine; the firm is not a Merton object</td>
                <td>A scope definition, and a correct exclusion</td>
                <td className="num">{m?.exclusion_families['model_inapplicability'] ?? '—'}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="prose">
          Limited partnerships, royalty and statutory trusts and special-purpose
          entities fall in the second family. Merton prices equity as a call option
          on firm assets; a partnership interest is not that instrument, so such a
          registrant does not belong in the cohort even when its data is complete.
          Financial firms sit awkwardly across both and are handled by the sector
          panel rather than a code — see <Link href="/case-studies">Case studies</Link>.
        </p>
      </section>

      <section className="section">
        <h2>Sample construction</h2>
        <p className="prose">
          The matching rule was pre-registered in{' '}
          <span className="mono">docs/matching-spec.md</span>, committed before any
          matching code was written and before any treatment-firm price series was
          retrieved. Control matching is the easiest place in a study like this to
          cheat without noticing: once treatment paths are visible, every judgement
          about who counts as comparable gets pulled toward the set that makes the
          separation look cleaner.
        </p>
        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr><th>Parameter</th><th>Fixed in advance as</th></tr>
            </thead>
            <tbody>
              <tr><td>Event</td><td className="mono">Earliest 8-K Item 1.03 per CIK</td></tr>
              <tr><td>Covariate date</td><td className="mono">t − 24 months, point-in-time</td></tr>
              <tr><td>Calendar time</td><td className="mono">Exact match on anchor quarter</td></tr>
              <tr><td>Sector</td><td className="mono">Exact match on SIC division</td></tr>
              <tr><td>Size</td><td className="mono">log(total assets) decile, ±1</td></tr>
              <tr><td>Leverage</td><td className="mono">liabilities/assets decile, ±1</td></tr>
              <tr><td>Replacement</td><td className="mono">Without, across the whole study</td></tr>
              <tr><td>Tie-break</td><td className="mono">Assets gap, leverage gap, then CIK</td></tr>
            </tbody>
          </table>
        </div>
        <p className="prose">
          Five amendments have been made since, each in its own commit with a stated
          reason: the ratio table corrected, the provenance tier renamed, calendar
          time promoted to an explicit matching variable, the control-eligibility
          rule reversed so that firms defaulting <em>after</em> a treatment
          firm&rsquo;s event are retained and censored rather than excluded, and
          era-conditional reporting extended from headline metrics to every
          descriptive cross-tab.
        </p>
        <p className="prose">
          The fourth changes matched sets: excluding later-defaulting controls would
          have biased the false-positive rate — the single number this study exists
          to produce — low. The fifth was forced by a published finding that turned
          out to be the era gradient measured a second time under another name; the
          original rule covered headline metrics but not the audit&rsquo;s own
          cross-tabs, so it was extended rather than narrowed.
        </p>
      </section>

      <section className="section">
        <h2>Limitations</h2>
        <div className="callout">
          <p className="eyebrow">Stated, not buried</p>
          <p>
            <strong>Period selection.</strong> The usable window is 2012–2024. Two
            structural thresholds cause this and neither can be worked around with
            free data. The sample is therefore a period of historically low default
            rates with no systemic credit event, and discriminatory power measured on
            it does not generalise to a crisis.
          </p>
          <p>
            <strong>Survivorship, both sides.</strong> Treatment firms enter only if
            their ticker resolves and their prices survive; controls are drawn from a
            point-in-time filer universe specifically to avoid the mirror-image bias
            of sampling firms still listed today.
          </p>
          <p>
            <strong>Selection into the cohort is not random.</strong> It is
            overwhelmingly a matter of <em>when</em> a firm failed: resolution
            runs from 12.8% to 68.7% across the window, so the cohort is heavily
            late. Once era is held fixed, most other apparent gradients stop
            being gradients — a size effect published earlier does not replicate
            at all. A sector effect does survive: mining resolves below its own
            era throughout. The cohort also under-samples financials, which
            flatters the headline result. Every cross-tab on{' '}
            <Link href="/measurement">Measurement</Link> is reported within era
            strata with its cell counts, for this reason.
          </p>
          <p>
            <strong>The benchmark is a cohort, not an issuer.</strong> Issuer-level
            bond pricing requires TRACE, which is not freely available. The mispricing
            module therefore reports direction, not level.
          </p>
          <p>
            <strong>Quota-constrained design.</strong> The control ratio was set by a
            price-API monthly symbol cap, not by statistical power, and size is
            matched on book assets rather than market cap for the same reason.
          </p>
          {m && (
            <p>
              <strong>Current sample state.</strong> {m.resolved} of{' '}
              {m.total_candidates} sampled bankruptcy filings resolve (
              {pct(m.resolution_rate)}). Full breakdown on{' '}
              <Link href="/measurement">Measurement</Link>.
            </p>
          )}
        </div>
      </section>

      <section className="section">
        <h2>Reproduction</h2>
        <div className="eq">
          python -m scripts.audit_resolution --start 2010 --end 2024 --per-year 25
          <br />
          python -m scripts.verify_filing_text --n 80
          <br />
          python -m scripts.build_site_data
          <br />
          python -m scripts.smell_test
          <br />
          cd frontend &amp;&amp; npm run build
        </div>
        <p className="prose">
          Model scripts write deterministic CSVs to{' '}
          <span className="mono">data/processed/</span>. Random seeds are fixed; the
          matching procedure consults no RNG at all, because its tie-break is a total
          order. <span className="mono">FRED_API_KEY</span> is the only credential,
          it is read at build time only, and it never reaches a browser.
        </p>
      </section>
    </div>
  )
}
