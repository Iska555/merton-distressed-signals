/**
 * The Merton payoff: equity as a call option on the firm's assets.
 *
 * Static SVG, no data dependency, safe to render anywhere. It exists on the
 * homepage as a graphic rather than as an illustration of an argument made
 * elsewhere: the whole model follows from the kink at D, so showing the kink
 * is showing the thesis.
 */
export default function PayoffDiagram({
  height = 260,
  showLabels = true,
}: {
  height?: number
  showLabels?: boolean
}) {
  const W = 460
  const H = height
  const pad = { l: 44, r: 18, t: 18, b: 34 }
  const x = (v: number) => pad.l + (v / 100) * (W - pad.l - pad.r)
  const y = (v: number) => H - pad.b - (v / 100) * (H - pad.t - pad.b)
  const D = 55 // default barrier, in the same 0..100 asset units

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Equity payoff at maturity is zero until asset value reaches the debt face value, then rises one for one. Debt is the mirror image and is capped."
    >
      {/* axes */}
      <line x1={x(0)} y1={y(0)} x2={x(100)} y2={y(0)} stroke="var(--rule-strong)" />
      <line x1={x(0)} y1={y(0)} x2={x(0)} y2={y(100)} stroke="var(--rule-strong)" />

      {/* the barrier */}
      <line
        x1={x(D)}
        y1={y(0)}
        x2={x(D)}
        y2={y(100)}
        stroke="var(--signal)"
        strokeDasharray="3 4"
        strokeWidth={1.5}
      />

      {/* debt payoff: rises to D then flat */}
      <path
        d={`M ${x(0)} ${y(0)} L ${x(D)} ${y(D)} L ${x(100)} ${y(D)}`}
        fill="none"
        stroke="var(--series-2)"
        strokeWidth={2}
        strokeDasharray="7 4"
      />

      {/* equity payoff: flat at zero then 45 degrees */}
      <path
        d={`M ${x(0)} ${y(0)} L ${x(D)} ${y(0)} L ${x(100)} ${y(100 - D)}`}
        fill="none"
        stroke="var(--series-1)"
        strokeWidth={2.5}
      />

      {showLabels && (
        <>
          <text className="tick" x={x(D)} y={y(0) + 16} textAnchor="middle">
            D
          </text>
          <text className="axis-label" x={x(100)} y={y(0) + 16} textAnchor="end">
            asset value at maturity
          </text>
          <text
            className="axis-label"
            x={x(0) - 8}
            y={y(50)}
            textAnchor="middle"
            transform={`rotate(-90 ${x(0) - 30} ${y(50)})`}
          >
            payoff
          </text>
          <text
            className="tick"
            x={x(88)}
            y={y(100 - D) - 6}
            textAnchor="end"
            fill="var(--series-1)"
          >
            equity
          </text>
          <text
            className="tick"
            x={x(88)}
            y={y(D) - 8}
            textAnchor="end"
            fill="var(--series-2)"
          >
            debt
          </text>
        </>
      )}
    </svg>
  )
}
