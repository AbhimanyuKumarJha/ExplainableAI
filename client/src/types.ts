export type Verdict = 'fake' | 'real'

export type LimeWeight = readonly [string, number]

export type BackendPrediction = {
  prediction: Verdict
  confidence: number
  explanation?: LimeWeight[]
  rag?: BackendRagEvidence
}

export type AnalysisResult = {
  id: string
  verdict: Verdict
  realProbability: number
  verdictConfidence: number
  explanation: LimeWeight[]
  rag: RagEvidence
  text: string
  createdAt: string
}

export type BackendRagArticle = {
  text?: string
  label?: Verdict
  score?: number
  subject?: string
  date?: string
}

export type BackendRagEvidence = {
  status?: string
  present?: boolean
  top_score?: number
  response?: string
  similar_articles?: BackendRagArticle[]
}

export type RagArticle = {
  text: string
  label: Verdict
  score: number
  subject: string
  date: string
}

export type RagEvidence = {
  status: string
  present: boolean
  topScore: number
  response: string
  similarArticles: RagArticle[]
}

export type RecentScan = {
  id: string
  title: string
  source: string
  verdict: Verdict
  confidence: number
  time: string
}
