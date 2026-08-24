import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="site">
      <div className="wrap fgrid">
        <span className="fmark">Distressed Credit Signals</span>
        <p>
          Live figures are computed from visible browser inputs or deterministic
          committed output. The empirical measurement study is withdrawn pending a
          complete census, with the defect and affected claims recorded on{' '}
          <Link href="/data">Data</Link>. Sources: SEC EDGAR and XBRL, SEC DERA
          Financial Statement Data Sets, and NYU Stern Damodaran synthetic-rating data.
        </p>
      </div>
    </footer>
  )
}
