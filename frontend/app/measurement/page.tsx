import Link from 'next/link'
import ConditionalTable from '@/components/ConditionalTable'
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

  const fa = m.float_availability
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
          resolved to a ticker whose price history is actually retrievable.{' '}
          <strong>Which ones survive is overwhelmingly a matter of when they
          failed</strong>, and once that is held fixed most of the other
          differences on this page stop being differences.
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
        <h2>Everything else is reported inside era</h2>
        <p className="prose">
          Era is the dominant axis of this dataset, so any variable correlated
          with era will reproduce the era gradient under its own name. Three
          cross-tabs were once reported here as independent gradients. At least
          one was era measured a second time.{' '}
          <strong>Size, sector and filer type are therefore published within era
          strata, with the cell count beside every figure</strong>, and a rate is
          withheld where the interval is too wide to say anything.
        </p>

        {fa && fa.agreement !== null && (
          <div className="callout">
            <p className="eyebrow">
              The size variable is partly an artefact of the filing rules
            </p>
            <p>
              Public float is read from{' '}
              <span className="mono">dei:EntityPublicFloat</span>, which is an
              XBRL tag. A filer with no XBRL instance therefore has no float{' '}
              <em>by construction</em> — not because it is small, but because it
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
              So the &ldquo;none reported&rdquo; band of a size table is largely
              the pre-XBRL population wearing a different label. That is a
              finding about the public record rather than about firm size, which
              is this study&rsquo;s actual subject.
            </p>
          </div>
        )}
      </section>

      <section className="section">
        <h2>Size — no gradient survives conditioning</h2>
        <p className="prose">
          In only one of the four eras where all three bands can be read does
          the rate rise with size. In two the middle band is highest; in one it
          is lowest. There is no consistent ordering at any level of
          conditioning — the pooled column on the right shows why the
          conditional cells matter.
        </p>

        <ConditionalTable
          table={m.by_size_era}
          label="Public float at last 10-K"
          maxWidth={m.min_reportable.max_wilson_width}
        />

        <div className="callout callout-neutral">
          <p className="eyebrow">Corrected twice — what actually changed</p>
          <p>
            An earlier run on 190 candidates reported float ≥ $200M resolving at
            79% against 51% below, and concluded the cohort skewed large. That
            was retracted here as small-sample noise.{' '}
            <strong>That retraction was right about the conclusion and wrong
            about the reason</strong>, and three things had moved at once, so
            nothing was identified. Holding each fixed in turn:
          </p>
          <ul className="prose">
            <li>
              <strong>The exclusion-taxonomy fix is not implicated.</strong> Run
              it on the same 346 candidates before and after and every float band
              is identical except &ldquo;none reported&rdquo;. It recovered five
              firms, all of them in that band.
            </li>
            <li>
              <strong>The year range is not implicated.</strong> The old sample
              ran 2006–2024. Restricted to 2010–2024 to match, its top band goes{' '}
              <em>up</em>, to 18 of 22.
            </li>
            <li>
              <strong>The resolver got stricter, and that is most of it.</strong>{' '}
              Nine firms present in both runs flipped from resolved to
              unresolved, seven of them to{' '}
              <span className="mono">AMBIGUOUS_OVERLAPPING</span> — the
              mutual-exclusivity guard added after the old run. On the seventeen
              top-band firms common to both samples, 15 of 17 became 11 of 17.
              Those resolutions were withdrawn because they were unsafe, not
              because the sample changed.
            </li>
            <li>
              <strong>The rest is ordinary imprecision.</strong> 18 of 22 against
              38 of 65 is not a significant difference (Fisher exact,{' '}
              <span className="tnum">p = 0.07</span>). The two intervals overlap.
            </li>
          </ul>
          <p>
            The honest account is not that the finding collapsed. It is that a
            point estimate was published without its interval, from a cell whose
            95% bounds ran from 61% to 93%. Nothing on this page now shows a rate
            without the count it rests on.
          </p>
        </div>
      </section>

      <section className="section">
        <h2>Sector — one effect survives, one does not</h2>
        <p className="prose">
          Sector composition varies sharply across eras: financials are 30% of
          2010–11 candidates and 5% of 2015–18; mining is 35% of 2015–18 and
          almost absent from 2022–24. A pooled sector rate is therefore partly a
          statement about when each sector failed.
        </p>

        <ConditionalTable
          table={m.by_sector_era}
          label="SIC division"
          maxWidth={m.min_reportable.max_wilson_width}
        />

        <div className="callout">
          <p className="eyebrow">Survives conditioning</p>
          <p>
            <strong>Mining resolves below its own era in every era where the
            cell can be read</strong> — 0 of 13, then 38% against an era average
            of 48%, then 47% against 57%. <strong>Manufacturing sits above its
            era in all five</strong>, every cell reportable, from 22% against
            13% to 82% against 69%. Those are sector effects, not era in
            disguise.
          </p>
        </div>

        <div className="callout callout-neutral">
          <p className="eyebrow">Does not survive conditioning</p>
          <p>
            The claim that financials resolve worst was carried by{' '}
            <strong>a single cell of fourteen firms in the worst era</strong>. In
            2010–11 financials are 1 of 14 against an era average of 13% — barely
            a gap — and every later financials cell is too small to report at
            all. The pooled figure is composition: financials are concentrated in
            the era where nothing resolves.
          </p>
          <p>
            What remains true is a fact about the cohort rather than about
            resolution: financials are 11.8% of candidates and 9.4% of the
            resolved set, so the study still under-samples the sector where
            Merton is least applicable. That direction is stated because it
            flatters the headline result.
          </p>
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
