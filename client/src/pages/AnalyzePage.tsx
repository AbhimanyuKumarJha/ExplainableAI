import { FileSearch } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { predictArticle } from '../api'
import { sampleArticle } from '../demoData'
import type { AnalysisResult } from '../types'
import { PageHeader } from '../components/ui/PageHeader'

type AnalyzePageProps = {
  onAnalysisComplete: (result: AnalysisResult) => void
}

export function AnalyzePage({ onAnalysisComplete }: AnalyzePageProps) {
  const navigate = useNavigate()
  const [text, setText] = useState(sampleArticle)
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const wordCount = useMemo(
    () => text.trim().split(/\s+/).filter(Boolean).length,
    [text],
  )

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (wordCount < 50) {
      setError('Paste at least 50 words so the model has enough context.')
      return
    }

    setIsLoading(true)
    try {
      const result = await predictArticle(text)
      onAnalysisComplete(result)
      navigate('/dashboard')
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? `${requestError.message}. Confirm the WSL FastAPI server is running on 127.0.0.1:8000.`
          : 'Prediction failed. Confirm the WSL FastAPI server is running.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="page page-narrow">
      <PageHeader
        eyebrow="Model-assisted verification"
        title="Analyze News Article"
        description="Submit article text for BiLSTM classification and LIME interpretation."
      />
      <form className="analysis-grid" onSubmit={handleSubmit}>
        <div className="panel input-panel">
          <div className="field-group">
            <label htmlFor="article-url">Source URL</label>
            <div className="url-row">
              <input
                id="article-url"
                placeholder="https://example.com/article"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
              />
              <button type="button" className="secondary-button" disabled>
                Fetch
              </button>
            </div>
          </div>
          <div className="field-group">
            <label htmlFor="article-text">Article Text</label>
            <textarea
              id="article-text"
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={15}
            />
          </div>
          {error ? <p className="form-error">{error}</p> : null}
          <div className="form-footer">
            <span>{wordCount} words</span>
            <button className="primary-button" type="submit" disabled={isLoading}>
              <FileSearch size={17} />
              {isLoading ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        </div>
        <aside className="panel status-panel">
          <div>
            <span className="meta-label">Pipeline Status</span>
            <h2>BiLSTM + LIME</h2>
            <p>
              Live classification is connected through the Vite proxy. RAG
              evidence uses demo fixtures until the backend exposes source
              retrieval.
            </p>
          </div>
          <div className="status-list">
            <StatusRow label="Classifier API" state="Live endpoint" />
            <StatusRow label="LIME Weights" state="From /predict" />
            <StatusRow label="RAG Sources" state="Demo evidence" />
          </div>
        </aside>
      </form>
    </section>
  )
}

function StatusRow({ label, state }: { label: string; state: string }) {
  return (
    <div className="status-row">
      <span>{label}</span>
      <strong>{state}</strong>
    </div>
  )
}
