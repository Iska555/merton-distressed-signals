import type { ConditionalTable as Table, Cell } from '@/lib/siteData'

/**
 * A cross-tab reported within era as well as pooled.
 *
 * Era is the dominant axis of this sample — two SEC filing-rule changes drive
 * resolution from 13% to 69% across the window — so any other variable
 * correlated with era reproduces the era gradient under its own name. Showing
 * the pooled column beside the conditional cells is the point: a reader has to
 * be able to watch a pooled difference dissolve when era is held fixed.
 *
 * Every cell carries its count. A rate is printed only when its 95% Wilson
 * interval is narrow enough to separate one band from another; otherwise the
 * counts stand alone. That is a floor, not a safeguard — see /measurement.
 */
function CellBox({ cell, pooled = false }: { cell: Cell; pooled?: boolean }) {
  if (cell.n === 0) {
    return (
      <td className="num" style={{ color: 'var(--faint)' }}>
        —
      </td>
    )
  }
  return (
    <td
      className="num"
      style={{
        background: pooled ? 'var(--surface)' : undefined,
        whiteSpace: 'nowrap',
      }}
    >
      <span className="tnum" style={{ fontSize: 12, color: 'var(--muted)' }}>
        {cell.resolved}/{cell.n}
      </span>
      <br />
      {cell.reportable && cell.rate !== null ? (
        <span className="tnum" style={{ fontWeight: 500 }}>
          {(cell.rate * 100).toFixed(0)}%
        </span>
      ) : (
        <span
          className="tnum"
          style={{ color: 'var(--faint)' }}
          title="95% Wilson interval too wide to report a rate"
        >
          ±
        </span>
      )}
    </td>
  )
}

export default function ConditionalTable({
  table,
  label,
  maxWidth,
}: {
  table: Table
  label: string
  maxWidth: number
}) {
  return (
    <>
      <div className="scroll-x">
        <table className="data">
          <thead>
            <tr>
              <th>{label}</th>
              {table.eras.map((e) => (
                <th key={e} className="mono" style={{ textAlign: 'right' }}>
                  {e}
                </th>
              ))}
              <th style={{ textAlign: 'right', background: 'var(--surface)' }}>
                pooled
              </th>
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row) => (
              <tr key={row.label}>
                <td className="mono">{row.label}</td>
                {row.cells.map((c, i) => (
                  <CellBox key={table.eras[i]} cell={c} />
                ))}
                <CellBox cell={row.pooled} pooled />
              </tr>
            ))}
            <tr style={{ borderTop: '2px solid var(--rule)' }}>
              <td style={{ fontWeight: 500 }}>all candidates</td>
              {table.all.cells.map((c, i) => (
                <CellBox key={table.eras[i]} cell={c} />
              ))}
              <CellBox cell={table.all.pooled} pooled />
            </tr>
          </tbody>
        </table>
      </div>
      <p className="source-line">
        Each cell is resolved/candidates above the rate.{' '}
        <span className="tnum">±</span> means the 95% Wilson interval is wider
        than {(maxWidth * 100).toFixed(0)} points — the counts are real, the
        rate is not reportable. Suppression is on interval width rather than a
        count threshold because an extreme rate is estimated precisely at small
        n: 0 of 13 says something, 6 of 13 does not.
      </p>
    </>
  )
}
