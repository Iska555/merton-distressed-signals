/** Deterministic public data read by the live static research routes. */
import fs from 'node:fs'
import path from 'node:path'

const DIR = path.join(process.cwd(), 'public', 'data')

export interface Manifest {
  schema_version: number
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

export const getManifest = () => readJson<Manifest>('MANIFEST.json')
