import Link from 'next/link'
import BaseRateExplorer from './BaseRateExplorer'

export default function DiscriminationPage() {
  return (
    <div className="wrap">
      <header className="masthead">
        <p className="eyebrow">Discrimination · the cost of acting</p>
        <h1>A good AUC can still be useless in production.</h1>
        <p className="lede">
          Anyone can show distance to default falls before a bankruptcy. The question
          that matters is what the model does on firms that do not fail, and what that
          costs once you apply a realistic default rate. That arithmetic does not
          need the sample, so it is below and live.
        </p>
      </header>

      <BaseRateExplorer />

      <section className="section">
        <h2>Measured discrimination</h2>
        <div className="callout callout-neutral">
          <p className="eyebrow">Awaiting sample</p>
          <p>
            ROC curves and AUC by horizon, bootstrapped confidence intervals, the
            calibration plot and the lead-time distribution all require the matched
            cohort. Sample construction is in progress; see{' '}
            <Link href="/measurement">Measurement</Link>.
          </p>
          <p>
            The analysis is written and tested, including a{' '}
            <strong>three-estimator horse race</strong> — KMV iterative solve,
            simultaneous solve, and the Bharath–Shumway naive approximation — on
            identical samples with a paired bootstrap on the AUC differences.
            Bharath and Shumway (2008) found the naive approximation forecasts default
            about as well as the full solve. If that replicates here on 2012–2024 data,
            the honest headline is that the sophisticated machinery buys little, and it
            will be reported that way.
          </p>
        </div>
      </section>

      <section className="section">
        <h2>Rules fixed before the data</h2>
        <ul className="spec-body" style={{ paddingLeft: 20 }}>
          <li>
            <strong>AUC, not accuracy.</strong> Accuracy on a sample selected for
            defaulting is meaningless — a model flagging every firm on earth scores
            100%. The predecessor to this project hardcoded exactly that.
          </li>
          <li>
            <strong>Bootstrap over firms, not firm-months.</strong> Consecutive months
            of one firm are not independent observations; resampling rows would shrink
            intervals by roughly the square root of months per firm and manufacture
            precision that does not exist.
          </li>
          <li>
            <strong>No threshold is fitted.</strong> Thresholds in the explorer above
            are reader-driven inputs, never values chosen by maximising a metric on the
            study sample.
          </li>
          <li>
            <strong>Primary metric pre-registered:</strong> AUC at the 12-month horizon,
            XBRL provenance tier, non-financial firms, KMV iterative estimator. Every
            other cut is secondary and labelled as such.
          </li>
        </ul>
      </section>
    </div>
  )
}
