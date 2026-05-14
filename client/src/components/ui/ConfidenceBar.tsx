import type { Verdict } from '../../types'
import { percent } from '../../utils/format'

export function ConfidenceBar({
  verdict,
  value,
}: {
  verdict: Verdict
  value: number
}) {
  return (
    <div className="confidence">
      <div className="confidence-track">
        <span
          className={verdict === 'fake' ? 'confidence-fill fake' : 'confidence-fill real'}
          style={{ width: percent(value) }}
        />
      </div>
      <strong>{percent(value)}</strong>
    </div>
  )
}
