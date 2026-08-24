import Link from 'next/link'
import SectionMark from '@/components/SectionMark'
import { getManifest } from '@/lib/siteData'

const REPOSITORY = 'https://github.com/Iska555/merton-distressed-signals'
const CENSUS_SPEC =
  `${REPOSITORY}/blob/main/docs/superpowers/specs/` +
  '2026-08-24-measurement-integrity-census-design.md'

export default function DataPage() {
  const manifest = getManifest()

  return (
    <div className="wrap">
      <header className="masthead">
        <div className="section-eyebrow">
          <SectionMark name="data" />
          <p className="eyebrow">Data &middot; provenance before precision</p>
        </div>
        <h1>Every live result traces to a source or a visible equation.</h1>
        <p className="lede">
          The public release separates interactive model output from empirical
          evidence. When an evidence pipeline failed review, its page and public data
          were withdrawn instead of being silently revised.
        </p>
      </header>

      <section
        id="measurement-correction"
        className="section"
        data-research-status="withdrawn"
        aria-labelledby="correction-title"
      >
        <div className="callout">
          <p className="eyebrow">Correction record &middot; 24 August 2026</p>
          <h2 id="correction-title">Measurement study withdrawn before publication.</h2>
          <p>
            Pre-publication review found that the collector building the bankruptcy
            candidate set advanced offsets by 10 while the SEC returned 100 results
            per response, then stopped after four requests. For 2016, 647 reported
            hits became 128 unique retrieved documents and 99 visible registrants
            before a 25-row selection was made.
          </p>
          <p>
            The endpoint ranked results by relevance rather than filing date. The
            retained observations therefore had no known inclusion probability. Every
            rate derived from that set is withdrawn, including the resolution
            headline, disclosure-era gradient and repeat-filing rate. Historical files
            remain in Git as correction evidence, not as current research output.
          </p>
          <p>
            The replacement is a complete census of SEC Item 1.03 filings from 2010
            through 2024, an operational registrant-case convention, point-in-time
            DERA eligibility and blinded verification. Results will be published
            whatever they show.
          </p>
          <p>
            <a href={CENSUS_SPEC}>Read the approved census specification</a>
            {' · '}
            <a href={`${REPOSITORY}/commits/main`}>Inspect the repository history</a>
          </p>
        </div>
      </section>

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
                <td>Registrant-case census under rebuild</td>
                <td className="mono">8-K Item 1.03</td>
                <td>Public, no key</td>
              </tr>
              <tr>
                <td>SEC XBRL company facts</td>
                <td>Debt, shares and point-in-time identity evidence</td>
                <td className="mono">data.sec.gov/api/xbrl</td>
                <td>Public, no key</td>
              </tr>
              <tr>
                <td>SEC DERA Financial Statement Data Sets</td>
                <td>Point-in-time filer universe and total-assets eligibility</td>
                <td className="mono">quarterly ZIP</td>
                <td>Public, no key</td>
              </tr>
              <tr>
                <td>Tiingo end-of-day prices</td>
                <td>Historical prices and symbol trading windows</td>
                <td className="mono">EOD API</td>
                <td>API key; plan storage terms apply</td>
              </tr>
              <tr>
                <td>Damodaran synthetic ratings</td>
                <td>January 2026 periodic credit benchmark</td>
                <td className="mono">ratings.html</td>
                <td>Public, no key</td>
              </tr>
              <tr>
                <td>FRED ICE BofA OAS indices</td>
                <td>Licensing review only; observations excluded</td>
                <td className="mono">ICE BofA OAS</td>
                <td>Publicly accessible, publication restricted</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="source-line">
          <a href="/data/SOURCES.json" download>
            Download the source and licensing registry
          </a>
          .
        </p>
      </section>

      <section className="section">
        <h2>Live committed outputs</h2>
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
          <p className="prose">
            No manifest found. Run{' '}
            <span className="mono">uv run --frozen python -m scripts.build_site_data</span>.
          </p>
        )}
        <p className="source-line">
          The manifest is deterministic. It contains versioned source provenance and
          no wall-clock timestamp or self-referential commit hash.
        </p>
      </section>

      <section className="section">
        <h2>Research populations under rebuild</h2>
        <p className="prose">
          The definitions below were fixed before the census results land. They are
          design commitments, not reported findings.
        </p>
        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr><th>Layer</th><th>Pre-registered rule</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>Registrant-case candidate</td>
                <td>Item 1.03 filings clustered by CIK in an anchored 24-month window</td>
              </tr>
              <tr>
                <td>Population 1</td>
                <td>Complete public-record coverage census, 2010 to 2024, no size floor</td>
              </tr>
              <tr>
                <td>Population 2</td>
                <td>Strict 2012 to 2024 subset with timely DERA assets of at least USD 50 million</td>
              </tr>
              <tr>
                <td>Event-time rule</td>
                <td>No filing, amendment, identity fact or price unavailable at the event may enter</td>
              </tr>
              <tr>
                <td>Verification</td>
                <td>Blinded 80-row adjudication with no blank verdicts</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>Exclusions retain their meaning, not their withdrawn counts</h2>
        <div className="scroll-x">
          <table className="data">
            <thead>
              <tr><th>Family</th><th>Meaning</th><th>Research implication</th></tr>
            </thead>
            <tbody>
              <tr>
                <td className="mono">data_unavailability</td>
                <td>The case belongs in the question; public sources cannot support it</td>
                <td>A limitation that may create selection bias</td>
              </tr>
              <tr>
                <td className="mono">model_inapplicability</td>
                <td>The record is available; the security is not a clean Merton object</td>
                <td>A declared scope boundary</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="prose">
          Limited partnerships, royalty trusts and special-purpose entities do not
          become ordinary corporate equity merely because their filings are machine
          readable. The <Link href="/case-studies">case studies</Link> show why data
          reach and model applicability must remain separate decisions.
        </p>
      </section>

      <section className="section">
        <h2>Current release boundary</h2>
        <div className="callout">
          <p>
            <strong>Live:</strong> the browser-based structural solver, independent
            synthetic-rating comparison, base-rate decision exhibit, illustrative
            boundary cases, and this provenance record.
          </p>
          <p>
            <strong>Held:</strong> all bankruptcy-sample rates, era comparisons,
            repeat-cluster estimates and empirical discrimination results.
          </p>
          <p>
            <strong>Not claimed:</strong> issuer-specific bond pricing, a live trading
            signal, historical default-model accuracy, or performance in a crisis.
          </p>
        </div>
      </section>

      <section className="section">
        <h2>Reproduce the public release</h2>
        <div className="eq">uv run --frozen python -m scripts.verify</div>
        <p className="prose">
          The gate regenerates deterministic assets and live site data, lints and
          builds the frontend, audits production npm
          dependencies, exercises the browser analytics integration and runs the
          Python test suite. Credentials never reach the browser.
        </p>
      </section>
    </div>
  )
}
