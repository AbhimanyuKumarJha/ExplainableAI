export type Verdict = 'fake' | 'real'

export type LimeWeight = readonly [string, number]

export type BackendPrediction = {
  prediction: Verdict
  confidence: number
  explanation: LimeWeight[]
}

export type AnalysisResult = {
  id: string
  verdict: Verdict
  realProbability: number
  verdictConfidence: number
  explanation: LimeWeight[]
  text: string
  createdAt: string
}

export type SourceEvidence = {
  domain: string
  title: string
  excerpt: string
  relevance: number
  date: string
}

export type RecentScan = {
  id: string
  title: string
  source: string
  verdict: Verdict
  confidence: number
  time: string
}
