import Link from 'next/link'
import Image from 'next/image'
import FigureBars from '@/components/FigureBars'
import PayoffDiagram from '@/components/PayoffDiagram'
import SectionMark from '@/components/SectionMark'
import { getManifest, getMeasurement, pct } from '@/lib/siteData'

export default function Home() {
  const m = getMeasurement()
  const manifest = getManifest()

  const first = m?.by_era[0]
  const last = m?.by_era[m.by_era.length - 1]

  return (
    <>
      {/* 1. Asymmetric hero */}
      <header className="hero home-hero">
        <picture className="hero-art hero-art-light">
          <source srcSet="/figures/hero-paths-light.png" type="image/png" />
          <Image
            src="/figures/hero-paths-light.png"
            width={2000}
            height={680}
            alt=""
            unoptimized
          />
        </picture>
        <picture className="hero-art hero-art-dark">
          <source srcSet="/figures/hero-paths-dark.png" type="image/png" />
          <Image
            src="/figures/hero-paths-dark.png"
            width={2000}
            height={680}
            alt=""
            unoptimized
            priority
          />
        </picture>
        <div className="wrap">
          <div className="hero-grid">
            <div className="hero-copy">
              <p className="kicker">Working paper &middot; August 2026</p>
              <h1>Most corporate bankruptcies cannot be studied.</h1>
              <p className="lead">
                Of {m?.total_candidates ?? 346} US bankruptcy filings sampled
                from 2010 to 2024, the ticker a firm actually traded under can be
                recovered for {m?.resolved ?? 149} of them. The rest are not
                missing by choice. They are unreachable from free public data,
                and the literature built on that data has never said so.
              </p>
            </div>
            <div className="bignum">
              <span className="n tnum">{m ? pct(m.resolution_rate) : '43.1%'}</span>
              <span className="cap">
                of sampled bankrupt US filers can be matched to the security they
                traded as, using public sources alone.
              </span>
            </div>
          </div>
          <div className="hero-rule" />
          <p className="hero-params mono">
            Hero simulation: sigma 34%, mu 5%, horizon 3 years, barrier 56,
            seed 1974.
          </p>
        </div>
      </header>

      {/* 2. Statistic strip */}
      <section className="strip">
        <div className="wrap">
          <div className="strip-grid">
            <div className="stat">
              <span className="v tnum">
                {m ? `${m.resolved} / ${m.total_candidates}` : '149 / 346'}
              </span>
              <span className="k">Candidates resolved</span>
              <span className="d">bankruptcy filings, 2010 to 2024</span>
            </div>
            <div className="stat">
              <span className="v tnum">
                {first && last
                  ? `${pct(first.rate, 1)} to ${pct(last.rate, 1)}`
                  : '12.8% to 68.7%'}
              </span>
              <span className="k">Era gradient</span>
              <span className="d">monotone, earliest to latest cohort</span>
            </div>
            <div className="stat">
              <span className="v tnum">2</span>
              <span className="k">Disclosure rules responsible</span>
              <span className="d">XBRL 2011, cover page 2019</span>
            </div>
            <div className="stat">
              <span className="v tnum">
                {m ? pct(m.chapter_22_count / m.total_candidates, 1) : '8.4%'}
              </span>
              <span className="k">Filed twice</span>
              <span className="d">same registrant, two bankruptcies</span>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Inverted deep band */}
      <section className="band">
        <div className="wrap">
          <div className="band-grid">
            <div className="stack">
              <p className="kicker on-deep">The central finding</p>
              <p className="pull">
                Whether a failed company can be studied at all depends on when it
                failed, and the reason is regulatory rather than economic.
              </p>
              <p>
                A firm that went bankrupt in 2023 leaves a machine-readable
                trading symbol in its own filings. A firm that went bankrupt in
                2013 does not, because the tag did not exist yet. Nothing about
                the two failures differs. Only the paperwork does.
              </p>
              <p>
                This is not a limitations paragraph at the back of a paper. It is
                the result.
              </p>
            </div>
            <div className="band-stats">
              <div className="band-stat">
                <span className="bn tnum">2011</span>
                <span className="bl">
                  XBRL instance documents begin appearing in filings
                </span>
              </div>
              <div className="band-stat">
                <span className="bn tnum">2019</span>
                <span className="bl">
                  FAST Act rule adds a trading symbol column to the cover page
                </span>
              </div>
              <div className="band-stat">
                <span className="bn tnum">2008</span>
                <span className="bl">
                  The largest default cluster in modern history, and out of reach
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Figure block */}
      <section className="sec">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Measurement</p>
            <h2>Identifiability more than quintupled, and no bankruptcy changed.</h2>
            <p className="lead">
              Resolution rate by filing era, holding method constant. The same
              pipeline, run against the same kind of company, returns a different
              answer depending only on the decade.
            </p>
          </div>

          {m ? (
            <FigureBars
              number="Figure 1"
              title="Share of bankruptcy filings resolvable to a traded symbol"
              source={`n = ${m.total_candidates} candidates from SEC 8-K Item 1.03 filings. Every cell count is published on the measurement page. ${
                manifest
                  ? `Generated ${manifest.generated_utc.slice(0, 10)} at commit ${manifest.git_commit}.`
                  : ''
              }`}
              bars={m.by_era.map((e, i) => ({
                label: e.label.replace('-', ' to 20'),
                pct: e.rate * 100,
                value: `${(e.rate * 100).toFixed(1)}%`,
                highlight: i === m.by_era.length - 1,
              }))}
            />
          ) : (
            <p className="prose">
              Figure data are unavailable. See the Data module for the published
              inputs and reproduction steps.
            </p>
          )}

          <figure className="sample-field-figure">
            <Image
              src="/figures/sample-field.svg"
              width={742}
              height={252}
              alt="Every bankruptcy candidate grouped by filing year and resolution outcome"
              unoptimized
            />
            <figcaption className="figcap">
              <span className="fignum">Figure 2</span>
              <span className="figtitle">
                Every bankruptcy candidate, by filing year and outcome
              </span>
              <span className="figsrc">
                {`n = ${m?.total_candidates ?? 346} candidates from SEC 8-K Item 1.03 filings. One square per filing; texture separates model inapplicability from data unavailability.`}
              </span>
            </figcaption>
          </figure>
        </div>
      </section>

      {/* 5. Bordered two-up */}
      <section className="sec tinted">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">What decides it</p>
            <h2>Two rules, eight years apart.</h2>
          </div>
          <div className="thresholds">
            <div className="thr">
              <span className="year tnum">2011</span>
              <h3>Machine-readable filings arrive</h3>
              <p className="what">
                XBRL instance documents start appearing at scale. Before this
                point a filing carries no structured data at all, so nothing in
                it can be read by a pipeline without parsing prose.
              </p>
            </div>
            <div className="thr">
              <span className="year tnum">2019</span>
              <h3>The symbol gets its own column</h3>
              <p className="what">
                The FAST Act Modernization rule adds a trading symbol field to
                the 10-K cover page. Open a 2011 cover page and the column is
                simply absent. The datum was never there to extract.
              </p>
            </div>
          </div>
          <p className="small narrow">
            Between those dates the symbol exists only in running prose, in
            sentences of the form <em>traded on the New York Stock Exchange
            under the symbol EK</em>. Recovering it that way carries 40 of the{' '}
            {m?.resolved ?? 149} resolutions, and it is why Kodak resolves to EK
            rather than to the KODK it trades as today.
          </p>
        </div>
      </section>

      {/* 6. Figure block, second kind: the model as a graphic */}
      <section className="sec">
        <div className="wrap">
          <div className="hero-grid" style={{ alignItems: 'center' }}>
            <div className="stack">
              <p className="kicker">The model</p>
              <h2>Equity is a call option on the firm.</h2>
              <p className="lead">
                Merton&rsquo;s 1974 insight is the kink in this diagram.
                Shareholders are paid nothing until the assets clear the debt,
                then take everything above it. Lenders own the rest and their
                upside is capped.
              </p>
              <p className="prose">
                Everything downstream follows from that single shape. Distance to
                default is how many standard deviations of asset value sit
                between a firm and the barrier, and it is recoverable from the
                equity market alone, which is why it can be computed for
                companies whose bonds never trade.
              </p>
              <p>
                <Link href="/model">Solve it in the browser</Link>
              </p>
            </div>
            <figure>
              <PayoffDiagram />
              <figcaption className="figcap">
                <span className="fignum">Figure 3</span>
                <span className="figtitle">Payoff at maturity against asset value</span>
                <span className="figsrc">
                  Schematic. D is the face value of debt at the horizon. Drawn
                  from the model, not from data.
                </span>
              </figcaption>
            </figure>
          </div>
        </div>
      </section>

      {/* 7. Card grid */}
      <section className="sec tinted">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">The study</p>
            <h2>Six completed modules, built to be checked.</h2>
          </div>
          <div className="cards">
            <Link className="card" href="/model">
              <SectionMark name="model" />
              <h3>The model</h3>
              <p>
                Merton solved live in the browser. Move leverage and volatility,
                watch distance to default and the implied spread follow.
              </p>
              <span className="go">Open the solver</span>
            </Link>
            <Link className="card" href="/mispricing">
              <SectionMark name="mispricing" />
              <h3>Mispricing</h3>
              <p>
                Where equity-implied risk and the January 2026 periodic
                synthetic-rating default-spread benchmark disagree, with the
                original circularity removed.
              </p>
              <span className="go">See the divergence</span>
            </Link>
            <Link className="card" href="/measurement">
              <SectionMark name="measurement" />
              <h3>Measurement</h3>
              <p>
                The resolution audit in full. Era, sector and size conditioned on
                each other, with cell counts beside every rate.
              </p>
              <span className="go">Read the audit</span>
            </Link>
            <Link className="card" href="/case-studies">
              <SectionMark name="cases" />
              <h3>Cases</h3>
              <p>
                Three completed boundary cases show where public data reach ends
                and where the model does not apply cleanly.
              </p>
              <span className="go">Read the cases</span>
            </Link>
            <Link className="card" href="/discrimination">
              <SectionMark name="discrimination" />
              <h3>Discrimination</h3>
              <p>
                What separation costs. Threshold slider, confusion matrix, and
                precision once a realistic base rate is applied.
              </p>
              <span className="go">Base rate exhibit live</span>
            </Link>
            <Link className="card" href="/data">
              <SectionMark name="data" />
              <h3>Data</h3>
              <p>
                Sources, exclusions split by cause, spec amendments, and every
                command needed to reproduce the figures.
              </p>
              <span className="go">Check the work</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 8. Pull quote */}
      <section className="sec warm">
        <div className="wrap">
          <div className="quote">
            <span className="bar" />
            <div>
              <blockquote>
                A sample selected on the outcome cannot measure accuracy. A model
                that flags every firm on earth scores 100% on it.
              </blockquote>
              <cite>
                Why the original version of this project claimed nothing worth
                claiming
              </cite>
            </div>
          </div>
        </div>
      </section>

      {/* 9. Scope columns */}
      <section className="sec">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Scope</p>
            <h2>What this is not.</h2>
          </div>
          <div className="scope">
            <div className="scopecol">
              <h3>Not an arbitrage signal</h3>
              <p>
                Issuer-level bond pricing needs TRACE, which is not free. The
                mispricing module compares an equity-implied estimate against the
                January 2026 periodic synthetic-rating default-spread benchmark,
                not against this firm&rsquo;s bond. It screens for disagreement and
                its direction. It is not basis points anyone could capture.
              </p>
            </div>
            <div className="scopecol">
              <h3>Not a crisis study</h3>
              <p>
                The usable window runs 2012 to 2024. Before 2011 the filings
                carry no XBRL, before 2019 no cover-page symbol. The 2008 default
                cluster is not merely absent from the sample. It is unreachable
                with free data, and any result here describes a low-default era.
              </p>
            </div>
            <div className="scopecol">
              <h3>Not an accuracy claim</h3>
              <p>
                This release makes no empirical discrimination claim. Any future
                AUC, false-positive rate and base-rate precision must be measured
                against a matched control cohort.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
