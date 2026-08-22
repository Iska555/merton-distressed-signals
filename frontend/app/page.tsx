import Link from 'next/link'
import { getManifest, getMeasurement, pct } from '@/lib/siteData'

export default function Home() {
  const m = getMeasurement()
  const manifest = getManifest()

  const early = m?.by_era.find((e) => e.label.startsWith('2012'))
  const late = m?.by_era.find((e) => e.label.startsWith('2022'))

  return (
    <div className="wrap">
      <header className="masthead">
        <p className="eyebrow">Abstract</p>
        <h1>
          Equity-implied credit risk, and what it costs to act on it.
        </h1>
        <p className="lede">
          Does distance to default, computed from a structural model on equity
          data alone, separate firms that subsequently default from comparable
          firms that do not — and what false-positive rate does that separation
          cost at realistic base rates?
        </p>
      </header>

      <section className="section">
        <h2>The finding so far is about measurement</h2>
        <p className="prose">
          The study was designed to test discrimination. Building it surfaced a
          prior problem that turns out to be the more useful result: constructing
          a survivorship-free sample of defaulted US firms from free public data
          is far harder than the literature admits, and the difficulty is
          <em> structured</em> — it varies systematically by era, by firm size and
          by sector, in ways that would bias any study that ignored them.
        </p>

        <div className="stat-row">
          <div className="stat">
            <div className="v tnum">{m ? pct(m.resolution_rate) : '—'}</div>
            <div className="k">Candidates resolvable</div>
            <div className="sub">
              {m ? `${m.resolved} of ${m.total_candidates} bankruptcy filings` : 'not yet computed'}
            </div>
          </div>
          <div className="stat">
            <div className="v tnum">
              {early && late ? `${pct(early.rate, 0)} → ${pct(late.rate, 0)}` : '—'}
            </div>
            <div className="k">Era gradient</div>
            <div className="sub">{early && late ? '2012–18 vs 2022–24' : 'not yet computed'}</div>
          </div>
          <div className="stat">
            <div className="v tnum">2</div>
            <div className="k">Structural thresholds</div>
            <div className="sub">XBRL ~2011, cover page 2019</div>
          </div>
        </div>

        <p className="source-line">
          Source: SEC EDGAR full-text search on 8-K Item 1.03, resolved against
          XBRL company facts.{' '}
          {manifest
            ? `Generated ${manifest.generated_utc.slice(0, 10)} at commit ${manifest.git_commit}.`
            : 'Manifest not found.'}{' '}
          Full method and exclusion rules on <Link href="/measurement">Measurement</Link>.
        </p>
      </section>

      <section className="section">
        <h2>Modules</h2>
        <div className="modules">
          <Link href="/model" className="module">
            <h3>The model</h3>
            <p>
              Merton (1974) from first principles, with an interactive solver that
              recovers asset value and asset volatility in your browser.
            </p>
            <span className="status">Live · no data needed</span>
          </Link>

          <Link href="/mispricing" className="module">
            <h3>Mispricing</h3>
            <p>
              Where equity-implied credit risk disagrees with what credit
              investors charge, on a benchmark rating assigned from accounting
              fundamentals alone.
            </p>
            <span className="status">Live · direction, not level</span>
          </Link>

          <Link href="/measurement" className="module">
            <h3>Measurement</h3>
            <p>
              Why the sample is hard to build: two XBRL thresholds, an era
              gradient, a size gradient, a spliced vendor ticker and a missing
              listing.
            </p>
            <span className="status">Computed</span>
          </Link>

          <Link href="/evidence" className="module">
            <h3>Evidence</h3>
            <p>
              Event-time distance-to-default paths, defaulted firms against
              matched surviving controls.
            </p>
            <span className="status">Awaiting sample</span>
          </Link>

          <Link href="/discrimination" className="module">
            <h3>Discrimination</h3>
            <p>
              ROC and AUC by horizon, an interactive threshold slider, and the
              base-rate-adjusted precision that follows from it.
            </p>
            <span className="status">Awaiting sample</span>
          </Link>

          <Link href="/data" className="module">
            <h3>Data</h3>
            <p>
              Sources with retrieval dates, sample construction, exclusions split
              by cause, downloads and limitations.
            </p>
            <span className="status">Computed</span>
          </Link>
        </div>
      </section>

      <section className="section">
        <h2>What this is not</h2>
        <div className="callout">
          <p className="eyebrow">Scope</p>
          <p>
            <strong>It is not an arbitrage signal.</strong> Issuer-level bond
            pricing requires TRACE, which is not freely available. The mispricing
            module compares an equity-implied estimate against a{' '}
            <em>rating-cohort index average</em>, not against this firm&rsquo;s
            bond. That is a screen for disagreement and its direction, never a
            number of basis points anyone could capture.
          </p>
          <p>
            <strong>It does not cover the financial crisis.</strong> The usable
            window is 2012–2024. Before roughly 2011 the filings carry no XBRL,
            and before 2019 they carry no trading symbol on the cover page at all.
            The 2008–09 default cluster is not merely absent; it is unreachable
            with free data.
          </p>
          <p>
            <strong>No accuracy claim is made from defaulted firms alone.</strong>{' '}
            A sample selected on the outcome cannot measure accuracy — a model
            that flags every firm on earth scores 100% on it. Discrimination is
            reported as AUC against a matched control cohort, with the
            false-positive rate stated.
          </p>
        </div>
      </section>
    </div>
  )
}
