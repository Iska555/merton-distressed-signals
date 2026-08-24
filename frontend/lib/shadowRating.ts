/**
 * Shadow credit rating, client side.
 *
 * Thresholds are NOT duplicated here. They are read from
 * public/data/shadow_rating.json, emitted by src/models/shadow_rating.py, so
 * the browser cannot hold a copy that has drifted from the study's.
 *
 * The rule this enforces: nothing derived from the Merton solve may enter the
 * benchmark rating. The inputs below are income-statement and balance-sheet
 * quantities only. If a future edit adds an asset-value or volatility argument,
 * the circularity is back and the comparison stops meaning anything.
 */

export interface BandDiagnostics {
  universeQuarter: string
  universeN: number
  p50AssetsUsd: number
  p75AssetsUsd: number
  p85AssetsUsd: number
  shareLargeAtThreshold: number
  within30PctOfBoundaryN: number
  shareWithin30PctOfBoundary: number
}

export interface RatingTables {
  large_cap: [number, string][]
  small_cap: [number, string][]
  large_cap_asset_threshold: number
  scale: string[]
  cohort_index: Record<string, string>
  source: Record<string, string>
  bandDiagnostics: BandDiagnostics
  benchmarkSpreadBps: Record<string, number>
  benchmarkSource: Record<string, string>
}

export interface Fundamentals {
  ebit: number
  interestExpense: number
  totalAssets: number
  totalDebt?: number
  ebitda?: number
  revenue?: number
}

export interface RatingResult {
  rating: string
  baseRating: string
  sizeBand: 'large' | 'small'
  coverage: number
  notch: number
  notchReason: string
  cohortIndex: string
  usable: boolean
  note: string
  nearBoundary: boolean
  bandForced: boolean
  naturalBand: 'large' | 'small'
}

export function shadowRating(
  f: Fundamentals,
  tables: RatingTables,
  forceBand?: 'large' | 'small' | null,
): RatingResult {
  const blank: RatingResult = {
    rating: '', baseRating: '', sizeBand: 'small', coverage: NaN,
    notch: 0, notchReason: '', cohortIndex: '', usable: false, note: '',
    nearBoundary: false, bandForced: false, naturalBand: 'small',
  }

  if (!f.totalAssets || f.totalAssets <= 0) {
    return { ...blank, note: 'total assets missing' }
  }

  const natural = f.totalAssets >= tables.large_cap_asset_threshold
  const large = forceBand ? forceBand === 'large' : natural
  const sizeBand: 'large' | 'small' = large ? 'large' : 'small'
  const table = large ? tables.large_cap : tables.small_cap

  // Firms near the cutoff have a rating that is partly an artefact of where the
  // boundary was drawn, so the page can say so rather than presenting it flat.
  const distance =
    Math.abs(f.totalAssets - tables.large_cap_asset_threshold) /
    tables.large_cap_asset_threshold
  const nearBoundary = distance <= 0.3

  let note = ''
  let coverage: number
  if (f.interestExpense <= 0) {
    coverage = Infinity
    note = 'no interest expense reported; coverage unbounded'
  } else {
    coverage = f.ebit / f.interestExpense
  }

  let base = 'D'
  for (const [minimum, rating] of table) {
    if (coverage >= minimum) {
      base = rating
      break
    }
  }

  // At most one notch, on the secondary ratios, with the reason recorded.
  let notch = 0
  let notchReason = ''
  const lev =
    f.totalDebt && f.ebitda && f.ebitda > 0 ? f.totalDebt / f.ebitda : null
  const margin = f.revenue && f.revenue > 0 ? f.ebit / f.revenue : null

  if (lev !== null && lev > 6.0) {
    notch = 1
    notchReason = `debt/EBITDA ${lev.toFixed(1)}x above 6.0`
  } else if (margin !== null && margin < 0) {
    notch = 1
    notchReason = `operating margin ${(margin * 100).toFixed(1)}% negative`
  } else if (lev !== null && lev < 1.5 && margin !== null && margin > 0.2) {
    notch = -1
    notchReason = `debt/EBITDA ${lev.toFixed(1)}x below 1.5 with operating margin ${(margin * 100).toFixed(1)}%`
  }

  const i = tables.scale.indexOf(base)
  const rating =
    notch === 0
      ? base
      : tables.scale[Math.max(0, Math.min(tables.scale.length - 1, i + notch))]

  return {
    rating,
    baseRating: base,
    sizeBand,
    coverage,
    notch,
    notchReason,
    cohortIndex: tables.cohort_index[rating] ?? 'BBB',
    usable: true,
    note,
    nearBoundary,
    bandForced: Boolean(forceBand),
    naturalBand: natural ? 'large' : 'small',
  }
}
