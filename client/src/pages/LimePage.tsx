import { ClipboardList, SlidersHorizontal } from 'lucide-react'
import { HighlightedText } from '../components/analysis/HighlightedText'
import { PageHeader } from '../components/ui/PageHeader'
import { SectionTitle } from '../components/ui/SectionTitle'
import type { AnalysisResult } from '../types'
import { formatDate, percent, titleFromText } from '../utils/format'

export function LimePage({ analysis }: { analysis: AnalysisResult }) {
  return (
    <section className="page">
      <PageHeader
        eyebrow={`Prediction ID: #${analysis.id}`}
        title="LIME Interpretation Analysis"
        description="Local Interpretable Model-agnostic Explanations for the latest prediction."
        action={
          <div className="compact-verdict">
            <span>
              Final Verdict <strong>{analysis.verdict.toUpperCase()}</strong>
            </span>
            <span>
              Confidence <strong>{percent(analysis.verdictConfidence)}</strong>
            </span>
          </div>
        }
      />
      <article className="panel legend-panel">
        <SectionTitle
          icon={<SlidersHorizontal size={18} />}
          title="Feature Importance Weighting"
        />
        <p>
          Highlight intensity correlates with feature contribution to the final
          prediction probability.
        </p>
        <div className="lime-scale" aria-label="LIME intensity scale">
          <span>Strong Fake Indicators</span>
          <div />
          <span>Strong Real Indicators</span>
        </div>
      </article>
      <article className="panel article-panel">
        <div className="article-source">
          <ClipboardList size={16} />
          Source: thedailywire-news.net (Unverified Domain)
        </div>
        <div className="article-body">
          <h2>{titleFromText(analysis.text)}</h2>
          <p className="byline">BY ANONYMOUS - {formatDate(analysis.createdAt)}</p>
          <HighlightedText text={analysis.text} weights={analysis.explanation} />
        </div>
      </article>
    </section>
  )
}
