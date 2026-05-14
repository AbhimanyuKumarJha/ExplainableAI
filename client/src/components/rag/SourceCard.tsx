import type { SourceEvidence } from '../../types'

export function SourceCard({ source }: { source: SourceEvidence }) {
  return (
    <article className="source-card">
      <div className="source-meta">
        <span>{source.domain.charAt(0)}</span>
        <strong>{source.domain}</strong>
        <em>High</em>
      </div>
      <h3>{source.title}</h3>
      <p>{source.excerpt}</p>
      <small>
        Relevance: {source.relevance.toFixed(2)} - Date: {source.date}
      </small>
    </article>
  )
}
