import type { AnalysisResult, RecentScan } from './types'

export const sampleArticle = `Global Financial Collapse Imminent: Insider Leaks Secret Plans for Digital Currency Confiscation.

In a shocking revelation that mainstream media is desperately trying to hide, high-level banking insiders have leaked documents detailing an imminent orchestrated collapse of the global financial system. The documents, dated October 15th, suggest that major central banks are preparing to transition to a unified digital currency.

However, the sinister truth behind this move is a planned mass confiscation of civilian wealth. According to the anonymous whistleblower, the new digital system will automatically freeze assets of anyone deemed a dissident by the shadow government.

"They are going to flip the switch at midnight on New Year's Eve. Your money will vanish instantly, replaced by compliance credits," the source warned ominously.`

export const fallbackAnalysis: AnalysisResult = {
  id: 'VAI-8892A',
  verdict: 'fake',
  realProbability: 0.058,
  verdictConfidence: 0.942,
  text: sampleArticle,
  createdAt: new Date().toISOString(),
  explanation: [
    ['shocking', -0.38],
    ['desperately', -0.35],
    ['hide', -0.3],
    ['imminent', -0.28],
    ['sinister', -0.45],
    ['mass', -0.46],
    ['confiscation', -0.5],
    ['major', 0.2],
    ['central', 0.22],
    ['banks', 0.2],
    ['documents', 0.18],
    ['freeze', -0.36],
    ['assets', -0.34],
    ['warned', -0.3],
    ['ominously', -0.33],
  ],
  rag: {
    status: 'present',
    present: true,
    topScore: 0.94,
    response:
      'The demo article is classified as fake because its strongest LIME terms are sensational claims such as "shocking", "sinister", and "confiscation". Similar retrieved records point to ordinary policy discussions rather than evidence for the article\'s extreme claims.',
    similarArticles: [
      {
        subject: 'politicsNews',
        label: 'real',
        text: 'Official coverage describes non-binding digital currency policy discussions and legislative requirements rather than an immediate global confiscation plan.',
        score: 0.94,
        date: 'Oct 15, 2023',
      },
      {
        subject: 'worldNews',
        label: 'real',
        text: 'Reuters reporting on finance ministers emphasized exploratory frameworks and local pilot programs for digital assets.',
        score: 0.88,
        date: 'Oct 16, 2023',
      },
      {
        subject: 'politicsNews',
        label: 'fake',
        text: 'A similar fake-style article used urgent language, anonymous sourcing, and unsupported claims about hidden government action.',
        score: 0.82,
        date: 'Oct 14, 2023',
      },
    ],
  },
}

export const recentScans: RecentScan[] = [
  {
    id: 'VAI-8892A',
    title: 'Financial Collapse Claims',
    source: 'thedailywire-news.net',
    verdict: 'fake',
    confidence: 0.942,
    time: '4 min ago',
  },
  {
    id: 'VAI-7320C',
    title: 'Regional Health Update',
    source: 'reuters.com',
    verdict: 'real',
    confidence: 0.884,
    time: '18 min ago',
  },
  {
    id: 'VAI-5148R',
    title: 'Election Technology Rumor',
    source: 'unverified-post.io',
    verdict: 'fake',
    confidence: 0.817,
    time: '42 min ago',
  },
]
