import fs from 'node:fs'
import path from 'node:path'
import Link from 'next/link'
import MispricingClient from './MispricingClient'
import SectionMark from '@/components/SectionMark'
import type { RatingTables } from '@/lib/shadowRating'

type RatingTablesPayload = Omit<
  RatingTables,
  'bandDiagnostics' | 'benchmarkSpreadBps' | 'benchmarkSource'
> & {
  band_diagnostics: {
    universe_quarter: string
    universe_n: number
    p50_assets_usd: number
    p75_assets_usd: number
    p85_assets_usd: number
    share_large_at_threshold: number
    within_30pct_of_boundary_n: number
    share_within_30pct_of_boundary: number
  }
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
        bandDiagnostics: {
          universeQuarter: payload.band_diagnostics.universe_quarter,
          universeN: payload.band_diagnostics.universe_n,
          p50AssetsUsd: payload.band_diagnostics.p50_assets_usd,
          p75AssetsUsd: payload.band_diagnostics.p75_assets_usd,
          p85AssetsUsd: payload.band_diagnostics.p85_assets_usd,
          shareLargeAtThreshold: payload.band_diagnostics.share_large_at_threshold,
          within30PctOfBoundaryN:
            payload.band_diagnostics.within_30pct_of_boundary_n,
          shareWithin30PctOfBoundary:
            payload.band_diagnostics.share_within_30pct_of_boundary,
        },
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
          Where the equity-implied estimate and periodic benchmark disagree.
        </h1>
        <p className="lede">
          The January 2026 periodic synthetic-rating default-spread benchmark gives
          the equity-implied estimate a fixed analytical reference. Their divergence
          is a screening direction, not a live market basis or a trade.
        </p>
      </header>

      {!tables && (
        <section className="section">
          <div className="callout">
            <p className="eyebrow">Not available</p>
            <p>
              Rating tables were not generated. Run{' '}
              <span className="mono">uv run --frozen python -m scripts.build_site_data</span>.
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
                ? (
                    <>
                      Table: {tables.source.table}, {tables.source.publisher}.{' '}
                      <strong>Large-firm verification:</strong>{' '}
                      {tables.source.large_verified}.{' '}
                      <strong>Small-firm verification:</strong>{' '}
                      {tables.source.small_verified}.
                    </>
                  )
                : ''}
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
