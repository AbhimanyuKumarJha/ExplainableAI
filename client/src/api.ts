import type { AnalysisResult, BackendPrediction } from './types'
import { env } from './config/env'

const clampProbability = (value: number) => Math.max(0, Math.min(1, value))

const makeAnalysisId = () =>
  `VAI-${Math.floor(1000 + Math.random() * 9000).toString()}${String.fromCharCode(
    65 + Math.floor(Math.random() * 26),
  )}`

export const normalizePrediction = (
  response: BackendPrediction,
  text: string,
): AnalysisResult => {
  const realProbability = clampProbability(response.confidence)
  const verdictConfidence =
    response.prediction === 'real' ? realProbability : 1 - realProbability

  return {
    id: makeAnalysisId(),
    verdict: response.prediction,
    realProbability,
    verdictConfidence: clampProbability(verdictConfidence),
    explanation: response.explanation ?? [],
    text,
    createdAt: new Date().toISOString(),
  }
}

export const predictArticle = async (text: string): Promise<AnalysisResult> => {
  const response = await fetch(`${env.apiBaseUrl}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw new Error(`Prediction failed with status ${response.status}`)
  }

  const payload = (await response.json()) as BackendPrediction
  return normalizePrediction(payload, text)
}
