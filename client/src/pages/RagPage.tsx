import { AlertTriangle, ClipboardList, Sparkles } from 'lucide-react'
import { SourceCard } from '../components/rag/SourceCard'
import { PageHeader } from '../components/ui/PageHeader'
import { SectionTitle } from '../components/ui/SectionTitle'
import { VerdictChip } from '../components/ui/VerdictChip'
import type { AnalysisResult } from '../types'
import { percent } from '../utils/format'

export function RagPage({ analysis }: { analysis: AnalysisResult }) {
  const { rag } = analysis

  return (
    <section className="page">
      <PageHeader
        eyebrow={`Analysis task ID-${analysis.id}`}
        title="RAG Evidence Verification"
        description="Retrieval-Augmented Generation breakdown for the latest analysis task."
      />
      <div className="rag-grid">
        <div className="rag-main">
          <article className="panel classification-panel">
            <div className="warning-box">
              <AlertTriangle size={27} />
            </div>
            <div>
              <h2>Classification: {analysis.verdict.toUpperCase()}</h2>
              <VerdictChip verdict={analysis.verdict} confidence={analysis.verdictConfidence} />
              <p>
                RAG status: {rag.status}. Top retrieval similarity:{' '}
                {percent(rag.topScore)}.
              </p>
            </div>
          </article>
          <article className="panel">
            <SectionTitle icon={<Sparkles size={18} />} title="Synthesized Explanation" />
            <p>{rag.response}</p>
          </article>
        </div>
        <aside className="rag-sources">
          <SectionTitle icon={<ClipboardList size={18} />} title="Source Verification" />
          {rag.similarArticles.length > 0 ? (
            rag.similarArticles.map((source, index) => (
              <SourceCard
                key={`${source.subject}-${source.score}-${index}`}
                source={source}
              />
            ))
          ) : (
            <p className="muted">No similar articles were returned by RAG.</p>
          )}
        </aside>
      </div>
    </section>
  )
}
