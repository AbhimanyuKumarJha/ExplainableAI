import type { LimeWeight } from '../../types'

export function LimeList({ weights }: { weights: LimeWeight[] }) {
  if (weights.length === 0) {
    return <p className="muted">No LIME terms returned yet.</p>
  }

  return (
    <div className="lime-list">
      {weights.map(([word, weight]) => (
        <div key={`${word}-${weight}`} className="lime-row">
          <span>{word}</span>
          <strong className={weight < 0 ? 'text-fake' : 'text-real'}>
            {weight.toFixed(3)}
          </strong>
        </div>
      ))}
    </div>
  )
}
