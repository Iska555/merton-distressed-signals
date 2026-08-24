import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="site">
      <div className="wrap fgrid">
        <span className="fmark">Distressed Credit Signals</span>
        <p>
          Every figure traces to committed output under{' '}
          <span className="mono">data/processed/</span> or to a computation shown
          on the page. Cell counts accompany every rate, and rates are suppressed
          where the confidence interval exceeds 50 points. Three findings have
          been retracted and corrected in place, each recorded on{' '}
          <Link href="/data">Data</Link> with what was claimed and why it was
          wrong. Sources: SEC EDGAR filings and XBRL, SEC DERA Financial
          Statement Data Sets, and NYU Stern Damodaran synthetic-rating data.
        </p>
      </div>
    </footer>
  )
}
