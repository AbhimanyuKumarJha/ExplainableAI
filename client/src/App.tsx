import { useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { fallbackAnalysis } from './demoData'
import { AnalyzePage } from './pages/AnalyzePage'
import { DashboardPage } from './pages/DashboardPage'
import { LimePage } from './pages/LimePage'
import { RagPage } from './pages/RagPage'
import type { AnalysisResult } from './types'
import './App.css'

function App() {
  const [analysis, setAnalysis] = useState<AnalysisResult>(fallbackAnalysis)

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          path="/analyze"
          element={<AnalyzePage onAnalysisComplete={setAnalysis} />}
        />
        <Route path="/dashboard" element={<DashboardPage analysis={analysis} />} />
        <Route path="/lime" element={<LimePage analysis={analysis} />} />
        <Route path="/rag" element={<RagPage analysis={analysis} />} />
        <Route path="*" element={<Navigate to="/analyze" replace />} />
      </Route>
    </Routes>
  )
}

export default App
