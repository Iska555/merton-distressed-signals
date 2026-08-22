'use client'

import { useEffect, useRef } from 'react'

/**
 * A bar chart treated as artwork rather than as decoration.
 *
 * Bars grow from zero when the figure scrolls into view, which gives a static
 * research page the movement a photograph would otherwise supply. Under
 * prefers-reduced-motion, and wherever IntersectionObserver is unavailable,
 * they are painted at full width immediately: the reader loses the animation
 * and loses nothing else, because the value is printed beside every bar.
 */
export interface Bar {
  label: string
  pct: number
  /** Printed at the right. Defaults to the percentage. */
  value?: string
  /** Copper rather than green. Use for the row the section is about. */
  highlight?: boolean
}

export default function FigureBars({
  bars,
  number,
  title,
  source,
  max = 100,
}: {
  bars: Bar[]
  number: string
  title: string
  source: string
  max?: number
}) {
  const root = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const node = root.current
    if (!node) return
    const rows = Array.from(node.querySelectorAll<HTMLElement>('.barrow'))
    const fill = (row: HTMLElement) => {
      const bar = row.querySelector<HTMLElement>('.barfill')
      if (bar) bar.style.width = `${row.dataset.pct ?? 0}%`
    }
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce || !('IntersectionObserver' in window)) {
      rows.forEach(fill)
      return
    }
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            fill(e.target as HTMLElement)
            io.unobserve(e.target)
          }
        }),
      { threshold: 0.35 },
    )
    rows.forEach((r) => io.observe(r))
    return () => io.disconnect()
  }, [bars])

  return (
    <figure>
      <div className="barchart" ref={root}>
        {bars.map((b) => (
          <div
            key={b.label}
            className={b.highlight ? 'barrow hi' : 'barrow'}
            data-pct={((b.pct / max) * 100).toFixed(1)}
          >
            <span className="barlab">{b.label}</span>
            <span className="bartrack">
              <span className="barfill" />
            </span>
            <span className="barval tnum">
              {b.value ?? `${b.pct.toFixed(1)}%`}
            </span>
          </div>
        ))}
      </div>
      <figcaption className="figcap">
        <span className="fignum">{number}</span>
        <span className="figtitle">{title}</span>
        <span className="figsrc">{source}</span>
      </figcaption>
    </figure>
  )
}
