import {
  CheckCircle2,
  ClipboardList,
  Gauge,
  LayoutDashboard,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'
import { recentScans } from '../demoData'
import type { AnalysisResult } from '../types'
import { LimeList } from '../components/analysis/LimeList'
import { RecentScanTable } from '../components/analysis/RecentScanTable'
import { ConfidenceBar } from '../components/ui/ConfidenceBar'
import { MetricCard } from '../components/ui/MetricCard'
import { PageHeader } from '../components/ui/PageHeader'
import { SectionTitle } from '../components/ui/SectionTitle'
import { percent } from '../utils/format'

export function DashboardPage({ analysis }: { analysis: AnalysisResult }) {
  const verdictTone = analysis.verdict === 'fake' ? 'danger' : 'success'

  return (
    <section className="page">
      <PageHeader
        eyebrow={`Analysis ID: #${analysis.id}`}
        title="Analysis Dashboard"
        description="Classification summary, model confidence, and explainability previews."
        action={<button className="secondary-button">Export PDF</button>}
      />
      <div className="dashboard-grid">
        <article className={`panel verdict-panel ${verdictTone}`}>
          {analysis.verdict === 'fake' ? (
            <ShieldAlert size={38} />
          ) : (
            <CheckCircle2 size={38} />
          )}
          <div>
            <span className="meta-label">Final Verdict</span>
            <h2>{analysis.verdict.toUpperCase()}</h2>
            <p>{percent(analysis.verdictConfidence)} confidence</p>
          </div>
        </article>
        <MetricCard label="Real Probability" value={percent(analysis.realProbability)} />
        <MetricCard
          label="Feature Signals"
          value={analysis.explanation.length.toString()}
        />
        <MetricCard
          label="Evidence Sources"
          value={analysis.rag.similarArticles.length.toString()}
        />
      </div>
      <div className="content-grid">
        <article className="panel">
          <SectionTitle icon={<Gauge size={18} />} title="Model Confidence" />
          <ConfidenceBar verdict={analysis.verdict} value={analysis.verdictConfidence} />
          <p className="muted">
            The backend returns confidence for the predicted label. The
            interface derives real probability from that same response.
          </p>
        </article>
        <article className="panel">
          <SectionTitle icon={<Sparkles size={18} />} title="LIME Preview" />
          <LimeList weights={analysis.explanation.slice(0, 5)} />
        </article>
        <article className="panel wide-panel">
          <SectionTitle icon={<LayoutDashboard size={18} />} title="Recent Scans" />
          <RecentScanTable scans={recentScans} />
        </article>
        <article className="panel">
          <SectionTitle icon={<ClipboardList size={18} />} title="RAG Summary" />
          <p>{analysis.rag.response}</p>
        </article>
      </div>
    </section>
  )
}
