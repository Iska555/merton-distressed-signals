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
/**
 * The ramp runs from the page ground to the primary red, so a low rate
 * recedes into the page and a high one advances out of it. Mixing against
 * tokens rather than baking hex means the same markup reads correctly in
 * both themes: the ground is white in light and near-black in dark, and the
 * direction of the ramp is preserved either way.
 */
const RAMP_CAP = 0.62

function shade(rate: number): string {
  const t = Math.max(0, Math.min(1, rate)) * RAMP_CAP
  return `color-mix(in srgb, var(--fig-primary) ${(t * 100).toFixed(1)}%, var(--ground))`
}

/**
 * One text colour across the whole ramp, which is why the ramp is capped.
 *
 * A full-range ground-to-red ramp passes through a band where neither the
 * body ink nor its inverse clears 4.5:1, in both themes. Capping the mix at
 * RAMP_CAP keeps every cell light enough (light theme) or dark enough (dark
 * theme) for --fig-ink, worst case 4.89:1. The legend swatches run through
 * the same function, so the scale a reader matches against is the scale the
 * cells are actually drawn on.
 */
function ink(): string {
  return 'var(--fig-ink)'
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
                          <span className="c" style={{ color: 'var(--muted)' }}>
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
                          <span className="r" style={{ color: 'var(--muted)' }}>
                            &plusmn;
                          </span>
                          <span className="c" style={{ color: 'var(--muted)' }}>
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
                        style={{ background: shade(c.rate), color: ink() }}
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
