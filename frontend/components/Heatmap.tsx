import type { ConditionalTable } from '@/lib/siteData'

/**
 * Resolution rate as an era-by-sector grid.
 *
 * This is the honest alternative to a photograph. It is a real image built
 * from the study's own data, it carries a section on its own, and every cell
 * prints the count it rests on, so shading never stands in for evidence.
 *
 * Cells whose 95% Wilson interval is too wide to read show their counts on a
 * flat tint instead of a shade. Colouring an unreadable cell would let a
 * reader infer a rate the data does not support, which is the exact failure
 * this page exists to document.
 */
function shade(rate: number): string {
  // Interpolate white to deep teal. Rate is already 0..1.
  const t = Math.max(0, Math.min(1, rate))
  const from = [255, 255, 255]
  const to = [13, 74, 71]
  const mix = from.map((f, i) => Math.round(f + (to[i] - f) * t))
  return `rgb(${mix[0]}, ${mix[1]}, ${mix[2]})`
}

/** White type once the ground is dark enough to need it. */
function ink(rate: number): string {
  return rate > 0.45 ? '#FFFFFF' : '#1E3033'
}

export default function Heatmap({
  table,
  rowLabel,
  minRowN = 9,
}: {
  table: ConditionalTable
  rowLabel: string
  minRowN?: number
}) {
  const rows = table.rows.filter((r) => r.pooled.n >= minRowN)

  return (
    <div className="stack">
      <div className="scroll-x">
        <table className="heat">
          <thead>
            <tr>
              <th className="rowhead">{rowLabel}</th>
              {table.eras.map((e) => (
                <th key={e}>{e}</th>
              ))}
              <th>pooled</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th className="rowhead">{row.label}</th>
                {[...row.cells, row.pooled].map((c, i) => {
                  if (c.n === 0) {
                    return (
                      <td key={i} className="empty">
                        <div className="cell">
                          <span className="c" style={{ color: '#5F7176' }}>
                            none
                          </span>
                        </div>
                      </td>
                    )
                  }
                  if (!c.reportable || c.rate === null) {
                    return (
                      <td key={i} className="empty">
                        <div className="cell">
                          <span className="r" style={{ color: '#5F7176' }}>
                            &plusmn;
                          </span>
                          <span className="c" style={{ color: '#5F7176' }}>
                            {c.resolved}/{c.n}
                          </span>
                        </div>
                      </td>
                    )
                  }
                  return (
                    <td key={i}>
                      <div
                        className="cell"
                        style={{ background: shade(c.rate), color: ink(c.rate) }}
                      >
                        <span className="r">{(c.rate * 100).toFixed(0)}%</span>
                        <span className="c">
                          {c.resolved}/{c.n}
                        </span>
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="heat-legend">
        <span>0%</span>
        <span className="heat-scale" aria-hidden>
          {[0, 0.2, 0.4, 0.6, 0.8, 1].map((t) => (
            <span key={t} style={{ background: shade(t) }} />
          ))}
        </span>
        <span>100% resolved</span>
        <span style={{ marginLeft: 8 }}>
          &plusmn; marks a cell whose interval is too wide to read. Counts shown,
          shade withheld.
        </span>
      </div>
    </div>
  )
}
