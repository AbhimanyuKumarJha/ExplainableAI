import { useMemo } from 'react'
import type { LimeWeight } from '../../types'
import { tokenKey } from '../../utils/format'

export function HighlightedText({
  text,
  weights,
}: {
  text: string
  weights: LimeWeight[]
}) {
  const weightMap = useMemo(() => {
    const entries = new Map<string, number>()
    weights.forEach(([word, weight]) => entries.set(tokenKey(word), weight))
    return entries
  }, [weights])

  return (
    <div className="highlighted-copy">
      {text.split(/(\s+)/).map((part, index) => {
        const key = tokenKey(part)
        const weight = weightMap.get(key)

        if (weight === undefined || key.length === 0) {
          return <span key={`${part}-${index}`}>{part}</span>
        }

        const strength =
          Math.abs(weight) > 0.35 ? 'strong' : Math.abs(weight) > 0.2 ? 'medium' : 'weak'
        const tone = weight < 0 ? 'fake' : 'real'

        return (
          <mark key={`${part}-${index}`} className={`${tone} ${strength}`}>
            {part}
          </mark>
        )
      })}
    </div>
  )
}
