import Link from 'next/link'

interface IllustrativeCase {
  name: string
  ticker: string
  event: string
  why: string
  fundamentals: string
  prices: string
}

/**
 * These are NOT computed. Each is here because the study cannot reach it, and
 * the reason is stated per firm. They sit in a visually distinct section
 * outside the computed study rather than alongside computed firms in identical
 * formatting -- that inconsistency is the first thing a hostile reader finds.
 */
const ILLUSTRATIVE: IllustrativeCase[] = [
  {
    name: 'Lehman Brothers Holdings',
    ticker: 'LEHMQ',
    event: '15 September 2008',
    why:
      'Falls outside the usable window entirely, and is unreachable in principle: ' +
      'pre-XBRL filings carry no machine-readable fundamentals and no cover-page ' +
      'trading symbol.',
    fundamentals:
      'None. CIK 0000806085 returns 404 from the XBRL company-facts API, and zero ' +
      'XBRL instance documents appear in any of its filings.',
    prices: 'Purged from every free source tested.',
  },
  {
    name: 'SVB Financial Group',
    ticker: 'SIVBQ',
    event: '10 March 2023',
    why:
      'Fundamentals are available, prices are not, and the model would not apply ' +
      'cleanly even if both were: this was a liquidity run, not an asset-value ' +
      'insolvency.',
    fundamentals:
      'Available through 2022-12-31. Total liabilities $195.50B, matching the final ' +
      '10-K before failure exactly.',
    prices:
      'SIVB and SIVBQ both return 404 from the free price source. SIVBQ exists in ' +
      'the vendor listing table but needs a credential the study does not have.',
  },
  {
    name: 'Credit Suisse Group',
    ticker: 'CS',
    event: '19 March 2023',
    why:
      'A foreign private issuer filing 20-F under the IFRS taxonomy, which exposes ' +
      'none of the us-gaap concepts the pipeline reads.',
    fundamentals:
      'None usable. 608 us-gaap concepts are present but there is no Liabilities ' +
      'tag and no standard debt concept among them.',
    prices: 'Purged from every free source tested.',
  },
]

export default function CaseStudies() {
  return (
    <div className="wrap">
      <header className="masthead">
        <p className="eyebrow">Case studies</p>
        <h1>The most instructive firms are the ones that cannot be computed.</h1>
        <p className="lede">
          Computed case studies require the matched sample. Until it lands, the only
          honest thing on this page is the set of firms that cannot be computed at
          all, which turns out to be more informative than it sounds, because the
          reasons differ and two of them are about the model rather than the data.
        </p>
      </header>

      <section className="section">
        <h2>Computed cases</h2>
        <div className="callout callout-neutral">
          <p className="eyebrow">Not yet computed</p>
          <p>
            Per-firm distance-to-default series, event annotations and a stated
            &ldquo;what the model missed&rdquo; section require the treatment cohort
            and its matched controls. Sample construction is in progress; its current
            state is on <Link href="/measurement">Measurement</Link>.
          </p>
          <p>
            When they land, each will carry a computed series with a month scrubber,
            and the set will include <strong>at least one documented failure</strong>{' '}
            a firm the model flagged that survived, or one that died with no
            warning. A study with no failures is advocacy rather than analysis.
          </p>
        </div>
      </section>

      <section className="section">
        <span className="flag">Illustrative, not sourced</span>
        <h2>Firms outside the study</h2>
        <p className="prose">
          Nothing in this section is computed from data. Each entry states why the
          firm cannot enter the sample. They are kept because the reasons are part of
          the finding, and separated because presenting them in the same format as
          computed results would misrepresent both.
        </p>

        {ILLUSTRATIVE.map((c) => (
          <div key={c.ticker} className="scroll-x">
            <table className="data">
              <thead>
                <tr>
                  <th colSpan={2}>
                    {c.name} · <span className="mono">{c.ticker}</span> · {c.event}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ width: 150, color: 'var(--muted)' }}>Why excluded</td>
                  <td>{c.why}</td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--muted)' }}>Fundamentals</td>
                  <td>{c.fundamentals}</td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--muted)' }}>Prices</td>
                  <td>{c.prices}</td>
                </tr>
              </tbody>
            </table>
          </div>
        ))}
      </section>

      <section className="section">
        <h2>Why Merton does not apply cleanly to banks</h2>
        <p className="prose">
          Two of the three firms above are banks, and the original build led with
          them while using a model that does not describe them. That is worth
          addressing directly rather than hoping nobody notices.
        </p>

        <div className="callout">
          <p className="eyebrow">The model assumes something banks violate</p>
          <p>
            <strong>Deposit funding is not ordinary debt.</strong> Merton treats debt
            as a single zero-coupon claim with a known face value maturing at a known
            date. Deposits are callable on demand, in full, by depositors acting
            simultaneously. There is no maturity at which the option is exercised;
            the barrier can be hit whenever confidence goes.
          </p>
          <p>
            <strong>SVB and Credit Suisse were liquidity runs, not asset-value
            insolvencies.</strong> SVB&rsquo;s securities portfolio had lost value to
            rate rises, but the firm failed because depositors withdrew faster than
            assets could be sold, not because assets fell below liabilities in the
            Merton sense. A model measuring the distance from asset value to a debt
            barrier is measuring the wrong distance.
          </p>
          <p>
            <strong>Opacity and off-balance-sheet exposure.</strong> The model reads
            the balance sheet it is given. For banks, a material part of the risk is
            not on it.
          </p>
          <p>
            <strong>The consequence for this study.</strong> Financial firms are
            retained in the sample but reported separately, never pooled into the
            headline. The pre-registered primary metric is computed on non-financials
            only. Because financials also resolve at a lower rate than other sectors,
            the cohort under-samples them anyway, which flatters the headline result
            and weakens the sector panel. Both directions are stated on{' '}
            <Link href="/measurement">Measurement</Link>.
          </p>
        </div>
      </section>

      <section className="section">
        <p className="source-line">
          Exclusion reasons above are drawn from live probes of the SEC XBRL
          company-facts API and the price vendor&rsquo;s public listing file, recorded
          in <span className="mono">docs/DECISIONS.md</span> (D2). No figure on this
          page is an empirical result about model performance.
        </p>
      </section>
    </div>
  )
}
