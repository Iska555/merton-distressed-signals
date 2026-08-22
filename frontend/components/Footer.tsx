import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="site">
      <div className="wrap" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <p>
          An empirical study of equity-implied credit risk, built from free public
          data. Every figure traces to a committed file under{' '}
          <span className="mono">data/processed/</span> or to a computation from
          inputs shown on screen. Anything not sourced is labelled in place.
        </p>
        <p>
          Sample construction, exclusion rules and limitations are set out on{' '}
          <Link href="/data">Data</Link>. Sources: SEC EDGAR (filings, XBRL
          fundamentals), SEC DERA Financial Statement Data Sets, FRED ICE BofA
          option-adjusted spread indices.
        </p>
      </div>
    </footer>
  )
}
