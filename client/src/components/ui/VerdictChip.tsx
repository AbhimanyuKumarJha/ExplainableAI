import type { Verdict } from '../../types'
import { percent } from '../../utils/format'

type VerdictChipProps = {
  verdict: Verdict
  confidence: number
  compact?: boolean
}

export function VerdictChip({
  verdict,
  confidence,
  compact = false,
}: VerdictChipProps) {
  return (
    <span className={`verdict-chip ${verdict} ${compact ? 'compact' : ''}`}>
      {verdict.toUpperCase()}
      {!compact ? ` ${percent(confidence)} CONFIDENCE` : ''}
    </span>
  )
}
