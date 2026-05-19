import type {
  AnalysisResult,
  BackendPrediction,
  BackendRagEvidence,
  RagEvidence,
  Verdict,
} from './types'
import { env } from './config/env'

const clampProbability = (value: number) => Math.max(0, Math.min(1, value))

const makeAnalysisId = () =>
  `VAI-${Math.floor(1000 + Math.random() * 9000).toString()}${String.fromCharCode(
    65 + Math.floor(Math.random() * 26),
  )}`

const normalizeVerdict = (label: unknown): Verdict =>
  label === 'real' ? 'real' : 'fake'

const normalizeLimeWeights = (weights?: unknown): AnalysisResult['explanation'] =>
  Array.isArray(weights)
    ? weights.flatMap((entry) => {
        if (!Array.isArray(entry) || entry.length < 2) {
          return []
        }

        const [word, weight] = entry
        const numericWeight = Number(weight)

        return typeof word === 'string' && Number.isFinite(numericWeight)
          ? [[word, numericWeight] as const]
          : []
      })
    : []

const normalizeRag = (rag?: BackendRagEvidence): RagEvidence => ({
  status: rag?.status ?? 'unavailable',
  present: Boolean(rag?.present),
  topScore: clampProbability(rag?.top_score ?? 0),
  response: rag?.response ?? 'No RAG explanation was returned by the server.',
  similarArticles:
    rag?.similar_articles?.map((article) => ({
      text: article.text ?? 'No source excerpt returned.',
      label: normalizeVerdict(article.label),
      score: clampProbability(article.score ?? 0),
      subject: article.subject?.trim() || 'Unknown subject',
      date: article.date?.trim() || 'Unknown date',
    })) ?? [],
})

export const normalizePrediction = (
  response: BackendPrediction,
  text: string,
): AnalysisResult => {
  const verdictConfidence = clampProbability(response.confidence)
  const verdict = normalizeVerdict(response.prediction)
  const realProbability =
    verdict === 'real' ? verdictConfidence : 1 - verdictConfidence

  return {
    id: makeAnalysisId(),
    verdict,
    realProbability: clampProbability(realProbability),
    verdictConfidence,
    explanation: normalizeLimeWeights(response.explanation),
    rag: normalizeRag(response.rag),
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
    const errorText = await response.text().catch(() => '')
    throw new Error(
      `Prediction failed with status ${response.status}${
        errorText ? `: ${errorText}` : ''
      }`,
    )
  }

  const payload = (await response.json()) as BackendPrediction
  return normalizePrediction(payload, text)
}
