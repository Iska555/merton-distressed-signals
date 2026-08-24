import Image from 'next/image'
import Link from 'next/link'
import PayoffDiagram from '@/components/PayoffDiagram'
import SectionMark from '@/components/SectionMark'

const CENSUS_SPEC =
  'https://github.com/Iska555/merton-distressed-signals/blob/main/' +
  'docs/superpowers/specs/2026-08-24-measurement-integrity-census-design.md'

export default function Home() {
  return (
    <>
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
              <p className="kicker">Structural credit research &middot; August 2026</p>
              <h1>Default risk starts inside the capital structure.</h1>
              <p className="lead">
                A live Merton solver recovers asset value and asset volatility from
                equity, then tests where market-implied risk diverges from an
                independent accounting benchmark. Every assumption is exposed.
              </p>
            </div>
            <div className="bignum">
              <span className="n">LIVE</span>
              <span className="cap">
                Two-equation structural solve, recomputed in the browser from the
                inputs you choose.
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

      <section className="strip">
        <div className="wrap">
          <div className="strip-grid">
            <div className="stat">
              <span className="v tnum">2</span>
              <span className="k">Unknowns solved jointly</span>
              <span className="d">asset value and asset volatility</span>
            </div>
            <div className="stat">
              <span className="v tnum">1e-8</span>
              <span className="k">Numerical tolerance</span>
              <span className="d">nested bisection, with failures surfaced</span>
            </div>
            <div className="stat">
              <span className="v tnum">Jan 2026</span>
              <span className="k">Periodic benchmark</span>
              <span className="d">Damodaran synthetic-rating table</span>
            </div>
            <div className="stat">
              <span className="v tnum">0</span>
              <span className="k">Issuer bond quotes claimed</span>
              <span className="d">screening direction, not a tradable basis</span>
            </div>
          </div>
        </div>
      </section>

      <section className="band">
        <div className="wrap">
          <div className="band-grid">
            <div className="stack">
              <p className="kicker on-deep">The research contribution</p>
              <p className="pull">
                A benchmark cannot challenge a model if it is built from the
                model&rsquo;s own answer.
              </p>
              <p>
                The earlier implementation inferred a shadow rating from
                model-implied leverage. That made the comparison self-referential.
                The current benchmark is assigned from accounting coverage, size,
                debt and margin data only. Changing asset value or volatility cannot
                move it.
              </p>
            </div>
            <div className="band-stats">
              <div className="band-stat">
                <span className="bn">Equity</span>
                <span className="bl">drives the structural market view</span>
              </div>
              <div className="band-stat">
                <span className="bn">Accounts</span>
                <span className="bl">drive the synthetic-rating benchmark</span>
              </div>
              <div className="band-stat">
                <span className="bn">Independent</span>
                <span className="bl">no asset-value feedback into the comparator</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="sec">
        <div className="wrap">
          <div className="hero-grid" style={{ alignItems: 'center' }}>
            <div className="stack">
              <p className="kicker">The model</p>
              <h2>Equity is a call option on the firm.</h2>
              <p className="lead">
                Shareholders receive nothing until assets clear the debt barrier,
                then own the residual. That option shape lets the equity market reveal
                an unobserved enterprise value and volatility.
              </p>
              <p className="prose">
                Move leverage, equity volatility, the risk-free rate and horizon.
                The solver recomputes distance to default, risk-neutral debt value and
                the structural debt spread without a server or a stored issuer result.
              </p>
              <p><Link href="/model">Open the structural solver</Link></p>
            </div>
            <figure>
              <PayoffDiagram />
              <figcaption className="figcap">
                <span className="fignum">Figure 1</span>
                <span className="figtitle">Payoff at maturity against asset value</span>
                <span className="figsrc">
                  Schematic computed from the Merton payoff. D is debt face value at
                  the horizon. No observed issuer data are used.
                </span>
              </figcaption>
            </figure>
          </div>
        </div>
      </section>

      <section className="sec tinted">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Mispricing</p>
            <h2>Two independent views of credit risk, one visible divergence.</h2>
            <p className="lead">
              The screen compares a structural equity-implied spread with a periodic
              synthetic-rating default-spread benchmark. It identifies disagreement,
              not an executable bond trade.
            </p>
          </div>
          <div className="thresholds">
            <div className="thr">
              <span className="year">Market</span>
              <h3>Structural debt view</h3>
              <p className="what">
                Equity value and volatility imply the value of risky debt under the
                Merton capital-structure model.
              </p>
            </div>
            <div className="thr">
              <span className="year">Accounts</span>
              <h3>Synthetic-rating view</h3>
              <p className="what">
                Interest coverage and issuer financials map independently to the
                January 2026 benchmark table.
              </p>
            </div>
          </div>
          <p><Link href="/mispricing">Stress the divergence</Link></p>
        </div>
      </section>

      <section
        className="sec warm"
        data-research-status="withdrawn"
        aria-labelledby="measurement-withdrawal"
      >
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Research correction &middot; 24 August 2026</p>
            <h2 id="measurement-withdrawal">Measurement study withdrawn before publication.</h2>
          </div>
          <div className="callout">
            <p>
              Pre-publication review found that the bankruptcy collector advanced
              offsets by 10 while the SEC returned 100 results per response, then
              stopped after four requests. For 2016, 647 reported hits became 128
              unique retrieved documents and 99 visible registrants before a 25-row
              selection was made.
            </p>
            <p>
              Results were relevance-ranked, not chronological, so the retained rows
              had no known inclusion probability. Every rate derived from that set is
              withdrawn. The route and its public data are withheld while the candidate
              set is rebuilt as a complete census. Results will be published whatever
              they show.
            </p>
            <p>
              <Link href="/data#measurement-correction">Read the correction record</Link>
              {' · '}
              <a href={CENSUS_SPEC}>Review the pre-registered census specification</a>
            </p>
          </div>
        </div>
      </section>

      <section className="sec">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Research terminal</p>
            <h2>Five live modules. One study held to a higher standard.</h2>
          </div>
          <div className="cards">
            <Link className="card" href="/model">
              <SectionMark name="model" />
              <h3>The model</h3>
              <p>Merton solved live, with convergence and assumptions exposed.</p>
              <span className="go">Open the solver</span>
            </Link>
            <Link className="card" href="/mispricing">
              <SectionMark name="mispricing" />
              <h3>Mispricing</h3>
              <p>Independent structural and accounting views of credit risk.</p>
              <span className="go">See the divergence</span>
            </Link>
            <Link className="card" href="/discrimination">
              <SectionMark name="discrimination" />
              <h3>Discrimination</h3>
              <p>Base-rate arithmetic, false positives and decision cost.</p>
              <span className="go">Use the base-rate exhibit</span>
            </Link>
            <Link className="card" href="/case-studies">
              <SectionMark name="cases" />
              <h3>Cases</h3>
              <p>Illustrative boundary cases, explicitly outside empirical results.</p>
              <span className="go">Read the cases</span>
            </Link>
            <Link className="card" href="/data">
              <SectionMark name="data" />
              <h3>Data</h3>
              <p>Sources, licensing, provenance and the public correction record.</p>
              <span className="go">Audit the work</span>
            </Link>
            <article className="card" data-research-status="withdrawn">
              <SectionMark name="measurement" />
              <h3>Measurement</h3>
              <p>The former sample is withdrawn. A complete Item 1.03 census is in progress.</p>
              <span className="flag">Held pending census</span>
            </article>
          </div>
        </div>
      </section>

      <section className="sec">
        <div className="wrap stack-lg">
          <div className="sec-head">
            <p className="kicker">Scope</p>
            <h2>What this release claims, and what it does not.</h2>
          </div>
          <div className="scope">
            <div className="scopecol">
              <h3>Structural, not executable</h3>
              <p>
                The mispricing screen has no issuer-specific bond quote. It compares
                two analytical views and reports direction, not capturable basis points.
              </p>
            </div>
            <div className="scopecol">
              <h3>Interactive, not fitted</h3>
              <p>
                Solver outputs respond only to inputs shown on screen. The base-rate
                exhibit uses reader-selected assumptions and makes no historical claim.
              </p>
            </div>
            <div className="scopecol">
              <h3>Corrected, not concealed</h3>
              <p>
                The empirical measurement page returns only after complete enumeration,
                point-in-time resolution and blinded verification pass their gates.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
