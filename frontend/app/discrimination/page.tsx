import BaseRateExplorer from './BaseRateExplorer'
import SectionMark from '@/components/SectionMark'

export default function DiscriminationPage() {
  return (
    <div className="wrap">
      <header className="masthead">
        <div className="section-eyebrow">
          <SectionMark name="discrimination" />
          <p className="eyebrow">Discrimination · the cost of acting</p>
        </div>
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
        <h2>Rules fixed before the data</h2>
        <ul className="spec-body" style={{ paddingLeft: 20 }}>
          <li>
            <strong>AUC, not accuracy.</strong> Accuracy on a sample selected for
            defaulting is meaningless. A model flagging every firm on earth scores
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
