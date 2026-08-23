import Link from 'next/link'
import Image from 'next/image'
import ConditionalTable from '@/components/ConditionalTable'
import Heatmap from '@/components/Heatmap'
import SectionMark from '@/components/SectionMark'
import { getManifest, getMeasurement, pct } from '@/lib/siteData'

export default function MeasurementPage() {
  const m = getMeasurement()
  const manifest = getManifest()

  if (!m) {
    return (
      <div className="wrap">
        <header className="masthead">
          <div className="section-eyebrow">
            <SectionMark name="measurement" />
            <p className="kicker">Measurement</p>
          </div>
          <h1>Not yet computed.</h1>
          <p className="lead">
            The audit output is absent from{' '}
            <span className="mono">data/processed/</span>. Run{' '}
            <span className="mono">python -m scripts.audit_resolution</span> then{' '}
            <span className="mono">python -m scripts.build_site_data</span>.
          </p>
        </header>
      </div>
    )
  }

  const fa = m.float_availability
  const unavailable = m.exclusion_families['data_unavailability'] ?? 0
  const inapplicable = m.exclusion_families['model_inapplicability'] ?? 0

  return (
    <>
      {/* Hero */}
      <header className="hero">
        <div className="wrap">
          <div className="hero-grid">
            <div className="hero-copy">
              <div className="section-eyebrow">
                <SectionMark name="measurement" />
                <p className="kicker">Measurement</p>
              </div>
              <h1>Which bankruptcies survive into a dataset is decided by the calendar.</h1>
              <p className="lead">
                Of {m.total_candidates} filings sampled from{' '}
                {m.window.sampled_from} to {m.window.sampled_to}, {m.resolved}{' '}
                resolve to a ticker whose price history is retrievable. Hold era
                fixed and most of the other differences on this page stop being
                differences.
              </p>
            </div>
            <div className="bignum">
              <span className="n tnum">{pct(m.resolution_rate)}</span>
              <span className="cap">
                resolved overall, against 12.8% in the earliest cohort and 68.7%
                in the latest.
              </span>
            </div>
          </div>
          <div className="hero-rule" />
        </div>
      </header>

      {/* Statistic strip */}
      <section className="strip">
        <div className="wrap">
          <div className="strip-grid">
            <div className="stat">
              <span className="v tnum">~2011</span>
              <span className="k">XBRL instances begin</span>
              <span className="d">no machine-readable filing data before</span>
            </div>
            <div className="stat">
              <span className="v tnum">2019</span>
              <span className="k">Cover-page symbol</span>
              <span className="d">FAST Act Modernization rule</span>
            </div>
            <div className="stat">
              <span className="v tnum">{unavailable}</span>
              <span className="k">Data unavailability</span>
              <span className="d">a limitation</span>
            </div>
            <div className="stat">
              <span className="v tnum">{inapplicable}</span>
              <span className="k">Model inapplicability</span>
              <span className="d">a scope definition</span>
            </div>
          </div>
        </div>
      </section>

      {/* Deep band: the thing that decides it */}
      <section className="band">
        <div className="wrap">
          <div className="band-grid">
            <div className="stack">
              <p className="kicker on-deep">Verified directly</p>
              <p className="pull">
                Kodak&rsquo;s 2011 cover page has no trading symbol on it,
                because the column did not exist.
              </p>
              <p>
                The page carries <em>Title of each Class</em> and{' '}
                <em>Name of each exchange on which registered</em>, and nothing
                else. Cover-page extraction, the obvious fallback for older
                filings, is not merely unreliable before 2019. The datum is not
                there.
              </p>
              <p>
                What survives is Item 5 prose, which states the symbol in a
                sentence: <em>traded on the New York Stock Exchange under the
                symbol EK</em>. That is the second provenance tier and it carries
                much of the pre-2019 sample.
              </p>
            </div>
            <div className="band-stats">
              {m.by_era.map((e) => (
                <div className="band-stat" key={e.label}>
                  <span className="bn tnum">{pct(e.rate, 0)}</span>
                  <span className="bl">
                    {e.label}, {e.resolved} of {e.n} resolved, {e.via_xbrl} via
                    XBRL and {e.via_text} via prose
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Figure 1: the era gradient */}
      <section className="sec">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">The era gradient</p>
            <h2>Identifiability more than quintupled, and no bankruptcy changed.</h2>
            <p className="lead">
              This is the single most consequential fact about the sample. The
              cohort piles up in the most recent years, which is a specific and
              unusual credit regime rather than a neutral period.
            </p>
          </div>

          <figure className="sample-field-figure">
            <Image
              src="/figures/sample-field.svg"
              width={742}
              height={252}
              alt="Every bankruptcy candidate grouped by filing year and resolution outcome"
              unoptimized
              priority
            />
            <figcaption className="figcap">
              <span className="fignum">Figure 1</span>
              <span className="figtitle">
                Every bankruptcy candidate, by filing year and outcome
              </span>
              <span className="figsrc">
                {`n = ${m.total_candidates} candidates from SEC 8-K Item 1.03 filings, resolved against XBRL company facts and Item 5 prose. One square represents one filing.`}
              </span>
            </figcaption>
          </figure>

          <div className="callout">
            <p className="eyebrow">Why this bounds the claim</p>
            <p>
              A sample concentrated in 2022 to 2024 is a sample of the fastest
              tightening cycle in forty years, the March 2023 regional bank
              failures, and a concentrated wave of rate-sensitive bankruptcies.
              The earlier window is a near-zero-rate era with historically
              suppressed default rates.{' '}
              <strong>
                Discriminatory power measured on one does not transfer to the
                other
              </strong>
              , so every headline metric is reported stratified by era rather
              than pooled. If the strata disagree, that is the result.
            </p>
          </div>
        </div>
      </section>

      {/* Figure 2: the heatmap */}
      <section className="sec tinted">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Sector against era</p>
            <h2>One sector effect survives conditioning. One does not.</h2>
            <p className="lead">
              Sector composition varies sharply across eras: financials are 30%
              of 2010 to 2011 candidates and 5% of 2015 to 2018. A pooled sector
              rate is therefore partly a statement about when each sector failed.
            </p>
          </div>

          <figure>
            <Heatmap table={m.by_sector_era} rowLabel="SIC division" />
            <figcaption className="figcap">
              <span className="fignum">Figure 2</span>
              <span className="figtitle">
                Resolution rate by sector within era, with cell counts
              </span>
              <span className="figsrc">
                Shading runs white to deep red across 0 to 100 percent. Divisions
                with fewer than nine candidates are omitted from the grid and
                appear in the full table below.
              </span>
            </figcaption>
          </figure>

          <div className="thresholds">
            <div className="thr">
              <span className="year tnum">Holds</span>
              <h3>Mining resolves below its own era, everywhere</h3>
              <p className="what">
                0 of 13, then 38% against an era average of 48%, then 47% against
                57%. Manufacturing sits above its era in all five, every cell
                reportable, from 22% against 13% up to 82% against 69%. These are
                sector effects, not era in disguise.
              </p>
            </div>
            <div className="thr">
              <span className="year tnum">Fails</span>
              <h3>Financials resolving worst was one small cell</h3>
              <p className="what">
                The claim rested on fourteen firms in 2010 to 2011, where the era
                average is 13% anyway, and every later financials cell is too
                small to report. The pooled gap is composition. What remains true
                is a fact about the cohort rather than a rate: financials are
                11.8% of candidates and 9.4% of the resolved set, so the study
                under-samples the sector where Merton is least applicable.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Size, and the confound */}
      <section className="sec">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Size</p>
            <h2>No size gradient survives conditioning.</h2>
            <p className="lead">
              Of the four eras in which all three bands can be read, the rate
              rises with size in exactly one. In two the middle band is highest;
              in one it is lowest.
            </p>
          </div>

          <ConditionalTable
            table={m.by_size_era}
            label="Public float at last 10-K"
            maxWidth={m.min_reportable.max_wilson_width}
          />

          {fa && fa.agreement !== null && (
            <div className="callout">
              <p className="eyebrow">
                The size variable is partly an artefact of the filing rules
              </p>
              <p>
                Public float is read from{' '}
                <span className="mono">dei:EntityPublicFloat</span>, which is an
                XBRL tag. A filer with no XBRL instance therefore has no float{' '}
                <em>by construction</em>, not because it is small but because it
                filed before 2011. The two line up on{' '}
                <strong>{pct(fa.agreement, 1)}</strong> of {fa.n} candidates.
              </p>
              <div className="scroll-x">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Filer has XBRL</th>
                      <th style={{ textAlign: 'right' }}>N</th>
                      <th style={{ textAlign: 'right' }}>Reports a public float</th>
                      <th style={{ textAlign: 'right' }}>Share</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fa.grid.map((g) => (
                      <tr key={String(g.any_xbrl)}>
                        <td className="mono">{g.any_xbrl ? 'yes' : 'no'}</td>
                        <td className="num">{g.n}</td>
                        <td className="num">{g.reports_float}</td>
                        <td className="num">{pct(g.share, 1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p>
                So the &ldquo;none reported&rdquo; band of a size table is
                largely the pre-XBRL population wearing a different label. That
                is a finding about the public record rather than about firm size,
                and the public record is this study&rsquo;s actual subject.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Pull quote */}
      <section className="sec warm">
        <div className="wrap">
          <div className="quote">
            <span className="bar" />
            <div>
              <blockquote>
                A point estimate was published without its interval, from a cell
                whose 95% bounds ran from 61% to 93%. The finding did not
                collapse. It was never that precise.
              </blockquote>
              <cite>
                On the size gradient, retracted at N = 346 and then the
                retraction itself corrected
              </cite>
            </div>
          </div>
        </div>
      </section>

      {/* Corrections */}
      <section className="sec">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Corrected in place</p>
            <h2>Three findings have been withdrawn, and one withdrawal was wrong.</h2>
          </div>

          <div className="callout callout-neutral">
            <p className="eyebrow">What actually changed</p>
            <p>
              An earlier run on 190 candidates reported float above $200M
              resolving at 79% against 51% below, and concluded the cohort skewed
              large. That was retracted here as small-sample noise.{' '}
              <strong>
                The retraction was right about the conclusion and wrong about the
                reason
              </strong>
              , and three things had moved at once, so nothing was identified.
              Holding each fixed in turn:
            </p>
            <ul>
              <li>
                <strong>The exclusion-taxonomy fix is not implicated.</strong>{' '}
                Run on the same {m.total_candidates} candidates before and after,
                every float band is identical except &ldquo;none reported&rdquo;.
                It recovered five firms, all in that band.
              </li>
              <li>
                <strong>The year range is not implicated.</strong> The old sample
                ran 2006 to 2024. Restricted to 2010 to 2024 to match, its top
                band goes <em>up</em>, to 18 of 22.
              </li>
              <li>
                <strong>The resolver got stricter, and that is most of it.</strong>{' '}
                Nine firms present in both runs flipped from resolved to
                unresolved, seven of them to{' '}
                <span className="mono">AMBIGUOUS_OVERLAPPING</span>, the
                mutual-exclusivity guard added after the old run. On the
                seventeen top-band firms common to both samples, 15 of 17 became
                11 of 17. Those resolutions were withdrawn because they were
                unsafe, not because the sample changed.
              </li>
              <li>
                <strong>The rest is ordinary imprecision.</strong> 18 of 22
                against 38 of 65 is not a significant difference (Fisher exact,{' '}
                <span className="tnum">p = 0.07</span>).
              </li>
            </ul>
            <p>
              Nothing on this page now shows a rate without the count it rests
              on. That is a floor and not a safeguard: the retracted cell has an
              interval only 31 points wide and would still be reported today.
            </p>
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
                    <td style={{ color: 'var(--muted)', fontSize: 12.5 }}>
                      {r.family.replace(/_/g, ' ')}
                    </td>
                    <td className="num">{r.n}</td>
                    <td className="num">{pct(r.share, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Two traps */}
      <section className="sec tinted">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Traps</p>
            <h2>Two ways this study could have failed silently.</h2>
          </div>
          <div className="scope">
            <div className="scopecol">
              <h3>The spliced ticker</h3>
              <p>
                Bed Bath &amp; Beyond traded near <strong>$0.07</strong> before
                its April 2023 filing. A major free price source returns a
                continuous BBBY series showing <strong>$19 to $36 and rising</strong>{' '}
                straight through the bankruptcy. Those are Overstock and Beyond
                Inc. prices, retro-mapped onto the recycled ticker. A pipeline
                trusting it would compute a healthy firm through a bankruptcy and
                record it as a model failure. Every series is validated against
                the symbol&rsquo;s own trading window before use, and rejected
                rather than repaired.
              </p>
            </div>
            <div className="scopecol">
              <h3>The concurrent symbol</h3>
              <p>
                A registrant cannot trade under two symbols at once, so two
                candidate symbols whose trading windows <em>overlap</em> cannot
                both belong to it. A genuine re-ticker shows a handoff instead:
                Walter Investment&rsquo;s WAC ends 2018-02-09 as Ditech&rsquo;s
                DHCP begins 2018-02-06. Overlapping candidates are flagged and{' '}
                <strong>never auto-ranked</strong>, because the data does not say
                which is right and ranking would silently choose one. The guard
                independently caught American Airlines, the AAL and AMR splice
                found by hand in Phase 0.
              </p>
            </div>
            <div className="scopecol">
              <h3>Chapter 22</h3>
              <p>
                {m.chapter_22_count} of {m.total_candidates} registrants, or{' '}
                {pct(m.chapter_22_count / m.total_candidates, 1)}, filed Item
                1.03 more than once. The first filing is the event, pre-registered
                before the sample was drawn, because the research question is
                about the onset of distress and keeping the last filing would
                discard exactly the transition under study.
              </p>
            </div>
          </div>

          <p className="source-line">
            Source: SEC EDGAR full-text search (8-K Item 1.03) and XBRL company
            facts; symbol windows from the price vendor&rsquo;s public listing
            file.{' '}
            {manifest
              ? `Generated ${manifest.generated_utc.slice(0, 10)} at commit ${manifest.git_commit} from data/processed/resolution_audit.csv.`
              : ''}{' '}
            Sample construction and full limitations on{' '}
            <Link href="/data">Data</Link>.
          </p>
        </div>
      </section>
    </>
  )
}
