import { AlertTriangle, ClipboardList, Sparkles } from 'lucide-react'
import { Contradiction } from '../components/rag/Contradiction'
import { SourceCard } from '../components/rag/SourceCard'
import { PageHeader } from '../components/ui/PageHeader'
import { SectionTitle } from '../components/ui/SectionTitle'
import { VerdictChip } from '../components/ui/VerdictChip'
import { sources } from '../demoData'
import type { AnalysisResult } from '../types'

export function RagPage({ analysis }: { analysis: AnalysisResult }) {
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
                The central claim is contradicted by official documentation and
                verified historical records of recent proceedings.
              </p>
            </div>
          </article>
          <article className="panel">
            <SectionTitle icon={<Sparkles size={18} />} title="Synthesized Explanation" />
            <p>
              Based on the retrieved corpus, the system identified several
              irreconcilable discrepancies between the analyzed article and
              verified authoritative sources.
            </p>
            <Contradiction
              title="Contradiction 1: Timeline & Authority"
              body="Official sources indicate the summit concluded with a non-binding framework, not a mandate. The WEF does not possess legislative authority to enforce a global currency timeline."
            />
            <Contradiction
              title="Contradiction 2: Attributed Quotes"
              body="A direct quote attributed to the IMF Director cannot be found in official transcripts. The transcript discusses localized pilot programs, contrary to the global rollout claim."
            />
          </article>
        </div>
        <aside className="rag-sources">
          <SectionTitle icon={<ClipboardList size={18} />} title="Source Verification" />
          {sources.map((source) => (
            <SourceCard key={source.domain} source={source} />
          ))}
        </aside>
      </div>
    </section>
  )
}
