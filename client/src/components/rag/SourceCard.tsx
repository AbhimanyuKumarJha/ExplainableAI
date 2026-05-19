import type { RagArticle } from '../../types'

export function SourceCard({ source }: { source: RagArticle }) {
  const sourceLabel = source.subject || source.label

  return (
    <article className="source-card">
      <div className="source-meta">
        <span>{sourceLabel.charAt(0).toUpperCase()}</span>
        <strong>{sourceLabel}</strong>
        <em>{source.label}</em>
      </div>
      <h3>Similarity match</h3>
      <p>{source.text}</p>
      <small>
        Score: {source.score.toFixed(2)} - Date: {source.date}
      </small>
    </article>
  )
}
