import Link from 'next/link'
import SectionMark from '@/components/SectionMark'

export default function EvidencePage() {
  return (
    <div className="wrap">
      <header className="masthead">
        <div className="section-eyebrow">
          <SectionMark name="evidence" />
          <p className="eyebrow">Evidence · event study</p>
        </div>
        <h1>The exhibit this study exists to produce does not exist yet.</h1>
        <p className="lede">
          The headline exhibit: median distance to default and its interquartile band
          from t−36 to t=0, defaulted firms against controls matched on calendar
          quarter, sector, size and leverage. If the bands separate cleanly and early,
          that is the finding. If they overlap until t−6, that is also the finding.
        </p>
      </header>

      <section className="section">
        <div className="callout callout-neutral">
          <p className="eyebrow">Awaiting sample</p>
          <p>
            This page is deliberately empty rather than populated with a placeholder
            chart. The event-time panel requires the treatment cohort, its matched
            controls and their price histories; sample construction is in progress and
            its current state is reported on <Link href="/measurement">Measurement</Link>.
          </p>
          <p>
            The analysis code is written and tested: event-time alignment, cohort
            bands with per-cell counts, a balanced-panel variant, and a
            composition table so a reader can tell a change in the firms from a change
            in <em>which</em> firms are present. What is missing is data, and inventing
            it would defeat the purpose of the study.
          </p>
        </div>
      </section>

      <section className="section">
        <h2>What will be shown, and how it will be qualified</h2>
        <ul className="spec-body" style={{ paddingLeft: 20 }}>
          <li>
            <strong>Median and IQR, not means.</strong> Distance to default is heavily
            skewed and unbounded above; one safe firm can move a mean visibly.
          </li>
          <li>
            <strong>Every band carries its own N.</strong> A band whose count collapses
            toward the edges of the window is evidence about who is still in the
            sample, not about firms.
          </li>
          <li>
            <strong>Stratified by era.</strong> 2012–18, 2019–21 and 2022–24 reported
            separately, because the sample spans a near-zero-rate period and the
            fastest tightening cycle in forty years, and discriminatory power does not
            transfer between them.
          </li>
          <li>
            <strong>Controls aligned on the treatment firm&rsquo;s event date</strong>,
            so both cohorts span the same calendar window and the comparison is not
            confounded with market-wide conditions.
          </li>
        </ul>
      </section>
    </div>
  )
}
