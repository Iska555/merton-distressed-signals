import fs from 'node:fs'
import path from 'node:path'
import Link from 'next/link'
import MispricingClient from './MispricingClient'
import SectionMark from '@/components/SectionMark'
import type { RatingTables } from '@/lib/shadowRating'

type RatingTablesPayload = Omit<
  RatingTables,
  'benchmarkSpreadBps' | 'benchmarkSource'
> & {
  benchmark_spread_bps: Record<string, number>
  benchmark_source: Record<string, string>
}

function readJson<T>(name: string): T | null {
  try {
    return JSON.parse(
      fs.readFileSync(path.join(process.cwd(), 'public', 'data', name), 'utf-8'),
    ) as T
  } catch {
    return null
  }
}

export default function MispricingPage() {
  const payload = readJson<RatingTablesPayload>('shadow_rating.json')
  const tables: RatingTables | null = payload
    ? {
        ...payload,
        benchmarkSpreadBps: payload.benchmark_spread_bps,
        benchmarkSource: payload.benchmark_source,
      }
    : null

  return (
    <div className="wrap">
      <header className="masthead">
        <div className="section-eyebrow">
          <SectionMark name="mispricing" />
          <p className="eyebrow">Mispricing · the divergence screen</p>
        </div>
        <h1>
          Where equity and credit disagree, and which way.
        </h1>
        <p className="lede">
          If the equity market implies a wider spread than credit investors are
          charging, one of the two is wrong. This is the part of the project with
          practical interest and the part that needs the most care, because the
          obvious way to build it does not work.
        </p>
      </header>

      {!tables && (
        <section className="section">
          <div className="callout">
            <p className="eyebrow">Not available</p>
            <p>
              Rating tables were not generated. Run{' '}
              <span className="mono">python -m scripts.build_site_data</span>.
            </p>
          </div>
        </section>
      )}

      {tables && <MispricingClient tables={tables} />}

      <section className="section">
        <details className="spec">
          <summary>How the benchmark rating is assigned</summary>
          <div className="spec-body">
            <p>
              <strong>Primary axis: interest coverage.</strong> EBIT divided by
              interest expense, mapped to a rating grade through the published
              synthetic-rating table, with separate large-cap and small-cap variants
              applied by size band.
            </p>
            <p>
              <strong>Size band from total assets, not market capitalisation.</strong>{' '}
              The published bands are stated on market cap, but market cap is a price,
              and prices are what the other side of this comparison is built from.
              Using it here would reintroduce a common input to both sides. This is a
              documented substitution, not a transcription.
            </p>
            <p>
              <strong>At most one notch</strong>, on debt/EBITDA or operating margin,
              with the notch and its reason recorded in the output so every assignment
              can be audited.
            </p>
            <p>
              {tables?.source
                ? `Table: ${tables.source.table}, ${tables.source.publisher}.`
                : ''}{' '}
              Threshold values are transcribed and carry a pending-verification flag
              until re-checked against the current published file; that flag is
              asserted by a test rather than left to memory.
            </p>
            <p>
              The benchmark is the January 2026 Damodaran synthetic-rating default
              spread, emitted from the same Python source as the rating tables. It is
              a periodic analytical input, not an ICE index, live credit price or
              issuer bond quote. Source and licensing details are listed on{' '}
              <Link href="/data">Data</Link>.
            </p>
          </div>
        </details>
      </section>
    </div>
  )
}
