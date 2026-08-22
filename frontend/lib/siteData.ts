/**
 * Static study data, read at build time.
 *
 * Research pages must render with the backend stopped, so nothing here fetches.
 * Files are produced by `python -m scripts.build_site_data` from committed CSVs
 * under data/processed/ and carry a MANIFEST recording the git commit and
 * provenance of every figure.
 *
 * When a file is absent the page renders a stated "not yet computed" panel
 * rather than a placeholder number. A missing result is a fact about the study,
 * not something to fill in.
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

export interface Measurement {
  total_candidates: number
  resolved: number
  resolution_rate: number | null
  by_year: YearRow[]
  by_era: EraRow[]
  by_size: BandRow[]
  by_sector: SectorRow[]
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
  x === null || x === undefined || !isFinite(x) ? '—' : (x * 100).toFixed(dp) + '%'
