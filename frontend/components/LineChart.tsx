'use client'

import { useRef, useState } from 'react'
import { niceTicks } from '@/lib/merton'

export interface Series {
  pts: [number, number][]
  color: string
  dash?: string
}

export interface Marker {
  x: number
  y: number
  color: string
  label: string
}

interface Props {
  series: Series[]
  xDomain: [number, number]
  yDomain: [number, number]
  xLabel: string
  yLabel: string
  xFmt: (t: number) => string
  yFmt: (t: number) => string
  ariaLabel: string
  marker?: Marker
  tip?: (xv: number) => string
}

const W = 460,
  H = 260,
  ML = 52,
  MR = 14,
  MT = 10,
  MB = 34
const IW = W - ML - MR,
  IH = H - MT - MB

export default function LineChart({
  series,
  xDomain,
  yDomain,
  xLabel,
  yLabel,
  xFmt,
  yFmt,
  ariaLabel,
  marker,
  tip,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [hover, setHover] = useState<{ rx: number; html: string; cx: number; cy: number } | null>(
    null,
  )

  const px = (x: number) => ML + ((x - xDomain[0]) / (xDomain[1] - xDomain[0])) * IW
  const py = (y: number) => MT + IH - ((y - yDomain[0]) / (yDomain[1] - yDomain[0])) * IH
  const clamp = (y: number) => Math.max(yDomain[0], Math.min(yDomain[1], y))

  const xTicks = niceTicks(xDomain[0], xDomain[1], 4)
  const yTicks = niceTicks(yDomain[0], yDomain[1], 4)

  function path(pts: [number, number][]): string {
    let d = ''
    for (const p of pts) {
      if (!isFinite(p[1])) continue
      d += (d === '' ? 'M' : 'L') + px(p[0]).toFixed(2) + ' ' + py(clamp(p[1])).toFixed(2)
    }
    return d
  }

  function onMove(e: React.MouseEvent<SVGRectElement>) {
    if (!tip || !svgRef.current) return
    const box = svgRef.current.getBoundingClientRect()
    const rx = ((e.clientX - box.left) / box.width) * W
    const xv = xDomain[0] + ((rx - ML) / IW) * (xDomain[1] - xDomain[0])
    setHover({ rx, html: tip(xv), cx: e.clientX, cy: e.clientY })
  }

  return (
    <>
      <svg
        ref={svgRef}
        className="chart"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={ariaLabel}
      >
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line
              x1={ML}
              x2={ML + IW}
              y1={py(t)}
              y2={py(t)}
              stroke="var(--grid)"
              strokeWidth={1}
            />
            <text x={ML - 8} y={py(t) + 3.5} textAnchor="end" className="tick">
              {yFmt(t)}
            </text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={`x${t}`} x={px(t)} y={MT + IH + 16} textAnchor="middle" className="tick">
            {xFmt(t)}
          </text>
        ))}

        <line
          x1={ML}
          x2={ML + IW}
          y1={MT + IH}
          y2={MT + IH}
          stroke="var(--rule-sw)"
          strokeWidth={1}
        />

        <text x={ML + IW / 2} y={H - 2} textAnchor="middle" className="axis-label">
          {xLabel}
        </text>
        <text
          textAnchor="middle"
          className="axis-label"
          transform={`translate(11,${MT + IH / 2}) rotate(-90)`}
        >
          {yLabel}
        </text>

        {series.map((s, i) => (
          <path
            key={i}
            d={path(s.pts)}
            fill="none"
            stroke={s.color}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            strokeDasharray={s.dash ?? 'none'}
          />
        ))}

        {marker && isFinite(marker.y) && (
          <g>
            <line
              x1={px(marker.x)}
              x2={px(marker.x)}
              y1={MT}
              y2={MT + IH}
              stroke="var(--rule-sw)"
              strokeWidth={1}
              strokeDasharray="3 3"
            />
            <circle
              cx={px(marker.x)}
              cy={py(clamp(marker.y))}
              r={6.5}
              fill={marker.color}
              stroke="var(--ground)"
              strokeWidth={2}
            />
            <text
              x={px(marker.x) > ML + IW * 0.68 ? px(marker.x) - 11 : px(marker.x) + 11}
              y={py(clamp(marker.y)) - 9}
              textAnchor={px(marker.x) > ML + IW * 0.68 ? 'end' : 'start'}
              className="tick"
              fontWeight={500}
              fill="var(--ink)"
            >
              {marker.label}
            </text>
          </g>
        )}

        {hover && (
          <line
            x1={hover.rx}
            x2={hover.rx}
            y1={MT}
            y2={MT + IH}
            stroke="var(--faint)"
            strokeWidth={1}
            opacity={0.5}
          />
        )}

        <rect
          x={ML}
          y={MT}
          width={IW}
          height={IH}
          fill="transparent"
          style={{ cursor: tip ? 'crosshair' : 'default' }}
          onMouseMove={onMove}
          onMouseLeave={() => setHover(null)}
        />
      </svg>

      {hover && hover.html && (
        <div
          className="tip"
          style={{
            opacity: 1,
            left: Math.min(hover.cx + 14, (typeof window !== 'undefined' ? window.innerWidth : 1000) - 200),
            top: hover.cy + 14,
          }}
          dangerouslySetInnerHTML={{ __html: hover.html }}
        />
      )}
    </>
  )
}
