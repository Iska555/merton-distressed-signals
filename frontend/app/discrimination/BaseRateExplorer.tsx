'use client'

import { useState } from 'react'

/**
 * Base-rate arithmetic. Needs no study data, which is why it ships now.
 *
 *   PPV = (TPR * pi) / (TPR * pi + FPR * (1 - pi))
 *
 * The point it makes is the most important honest finding available: a model
 * with a respectable AUC can be near-useless as a standalone alarm once the
 * base rate is realistic. Sliders are reader-driven inputs; nothing here is
 * fitted to any sample.
 */
export default function BaseRateExplorer() {
  const [tpr, setTpr] = useState(80)
  const [fpr, setFpr] = useState(20)
  const [baseRate, setBaseRate] = useState(1.5)

  const pi = baseRate / 100
  const t = tpr / 100
  const f = fpr / 100

  const truePos = t * pi
  const falsePos = f * (1 - pi)
  const flagged = truePos + falsePos
  const precision = flagged > 0 ? truePos / flagged : NaN
  const perTrue = truePos > 0 ? falsePos / truePos : Infinity

  // Per 10,000 firms, which is easier to reason about than probabilities.
  const N = 10000
  const tp = Math.round(truePos * N)
  const fp = Math.round(falsePos * N)
  const fn = Math.round((1 - t) * pi * N)
  const tn = Math.round((1 - f) * (1 - pi) * N)

  return (
    <section className="section">
      <h2>The base-rate exhibit</h2>
      <p className="prose">
        Set a sensitivity and a false-positive rate, then apply a realistic annual
        default rate. The precision that comes out is what a user of the signal
        would actually experience.
      </p>

      <div className="gap-panel">
        <div>
          <div className="field">
            <div className="field-head">
              <label htmlFor="tpr">Sensitivity · defaults caught</label>
              <output htmlFor="tpr" className="tnum">{tpr}%</output>
            </div>
            <input type="range" id="tpr" min={1} max={99} step={1} value={tpr}
              onChange={(e) => setTpr(+e.target.value)} />
          </div>
          <div className="field">
            <div className="field-head">
              <label htmlFor="fpr">False-positive rate · survivors flagged</label>
              <output htmlFor="fpr" className="tnum">{fpr}%</output>
            </div>
            <input type="range" id="fpr" min={1} max={60} step={1} value={fpr}
              onChange={(e) => setFpr(+e.target.value)} />
          </div>
          <div className="field">
            <div className="field-head">
              <label htmlFor="br">Annual default base rate</label>
              <output htmlFor="br" className="tnum">{baseRate.toFixed(1)}%</output>
            </div>
            <input type="range" id="br" min={0.2} max={15} step={0.1} value={baseRate}
              onChange={(e) => setBaseRate(+e.target.value)} />
          </div>
          <p style={{ fontSize: 12.5, color: 'var(--muted)' }}>
            The slider values are illustrative user-selected assumptions, not
            historical estimates or fitted study values. They span low-base-rate
            through severe-stress scenarios so you can inspect the arithmetic.
          </p>
        </div>

        <div>
          <div className="gapline">
            <div
              className="v tnum"
              style={{ color: precision < 0.2 ? 'var(--risk)' : 'var(--ink)' }}
            >
              {isFinite(precision) ? (precision * 100).toFixed(1) + '%' : 'n/a'}
            </div>
            <div className="k eyebrow">Precision · flagged firms that do default</div>
          </div>
          <div className="gapline">
            <div className="v tnum" style={{ fontSize: 24 }}>
              {isFinite(perTrue) ? perTrue.toFixed(1) : 'n/a'}
            </div>
            <div className="k eyebrow">False alarms per real default</div>
          </div>
          <p style={{ fontSize: 13.5, color: 'var(--muted)' }}>
            Out of <span className="mono tnum">{N.toLocaleString()}</span> firms:{' '}
            <span className="mono tnum">{tp}</span> correctly flagged,{' '}
            <span className="mono tnum">{fp}</span> falsely flagged,{' '}
            <span className="mono tnum">{fn}</span> missed,{' '}
            <span className="mono tnum">{tn.toLocaleString()}</span> correctly cleared.
          </p>
        </div>
      </div>

      <div className="scroll-x">
        <table className="data">
          <thead>
            <tr>
              <th>Per 10,000 firms</th>
              <th style={{ textAlign: 'right' }}>Defaults</th>
              <th style={{ textAlign: 'right' }}>Survivors</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Flagged</td>
              <td className="num">{tp}</td>
              <td className="num" style={{ color: 'var(--risk)' }}>{fp}</td>
            </tr>
            <tr>
              <td>Not flagged</td>
              <td className="num" style={{ color: 'var(--risk)' }}>{fn}</td>
              <td className="num">{tn.toLocaleString()}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="callout">
        <p className="eyebrow">Why this is the finding, not a caveat</p>
        <p>
          At the default settings, catching <strong>80%</strong> of defaults while
          flagging <strong>20%</strong> of survivors, against a{' '}
          <strong>1.5%</strong> base rate, precision is about{' '}
          <strong>5.7%</strong>. Roughly <strong>sixteen false alarms for every
          real default</strong>. The discriminatory power is genuine; the production
          experience is still mostly noise.
        </p>
        <p>
          This is not an argument that structural credit models are worthless. It is
          an argument that they are not standalone alarms. Used to rank a universe,
          or to decide where to spend analyst attention, a model with these
          properties is useful. Used to trigger an action on each flag, it is not.
          Saying so plainly is the difference between a study and a sales pitch.
        </p>
      </div>

      <p className="source-line">
        Computed in your browser from the sliders above. PPV = (TPR·π) / (TPR·π +
        FPR·(1−π)). No study data is involved and no threshold here is fitted.
      </p>
    </section>
  )
}
