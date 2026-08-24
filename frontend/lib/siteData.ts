/**
 * Static study data, read at build time.
 *
 * Research pages must render with the backend stopped, so nothing here fetches.
 * Files are produced by `python -m scripts.build_site_data` from committed CSVs
 * under data/processed/ and carry a MANIFEST recording the git commit and
 * provenance of every figure.
 *
 * When a required file is absent, the page renders a clear build/data error
 * rather than a placeholder number. Published routes require committed output.
 */
import fs from 'node:fs'
import path from 'node:path'

const DIR = path.join(process.cwd(), 'public', 'data')

export interface EraRow {
  label: string
  n: number
  resolved: number
  rate: number
  via_xbrl: number
  via_text: number
}
export interface YearRow { year: number; n: number; resolved: number; rate: number }
export interface BandRow { label: string; n: number; resolved: number; rate: number }
export interface SectorRow { sector: string; n: number; resolved: number; rate: number }
export interface ReasonRow { code: string; n: number; share: number; family: string }

/** One cell of an era-conditional cross-tab. `reportable` is false when the
 *  95% Wilson interval is too wide to separate this band from another; the
 *  counts are still shown, only the rate is withheld. */
export interface Cell {
  n: number
  resolved: number
  rate: number | null
  lo: number | null
  hi: number | null
  reportable: boolean
}
export interface ConditionalRow { label: string; cells: Cell[]; pooled: Cell }
export interface ConditionalTable {
  key: string
  eras: string[]
  rows: ConditionalRow[]
  all: { cells: Cell[]; pooled: Cell }
}
export interface FloatAvailability {
  grid: { any_xbrl: boolean; n: number; reports_float: number; share: number | null }[]
  by_era: { label: string; n: number; reports_float: number; any_xbrl: number }[]
  agreement: number | null
  n: number
}

export interface Measurement {
  total_candidates: number
  resolved: number
  resolution_rate: number | null
  by_year: YearRow[]
  by_era: EraRow[]
  by_size: BandRow[]
  by_sector: SectorRow[]
  by_size_era: ConditionalTable
  by_sector_era: ConditionalTable
  float_availability: FloatAvailability
  min_reportable: { max_wilson_width: number }
  reason_codes: ReasonRow[]
  exclusion_families: Record<string, number>
  chapter_22_count: number
  window: { sampled_from: number; sampled_to: number }
}

export interface Manifest {
  generated_utc: string
  git_commit: string
  files: Record<
    string,
    { source: string; rows_in: number; description: string; retrieved?: string }
  >
}

function readJson<T>(name: string): T | null {
  try {
    return JSON.parse(fs.readFileSync(path.join(DIR, name), 'utf-8')) as T
  } catch {
    return null
  }
}

export const getMeasurement = () => readJson<Measurement>('measurement.json')
export const getManifest = () => readJson<Manifest>('MANIFEST.json')

export const pct = (x: number | null | undefined, dp = 1) =>
  x === null || x === undefined || !isFinite(x) ? 'n/a' : (x * 100).toFixed(dp) + '%'
