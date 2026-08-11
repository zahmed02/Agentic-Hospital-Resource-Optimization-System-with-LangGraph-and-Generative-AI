'use client'

import { useState } from 'react'
import { clearCache, retrainModel } from '@/lib/api'

export default function SettingsPage() {
  const [cacheStatus, setCacheStatus] = useState<string | null>(null)
  const [trainStatus, setTrainStatus] = useState<string | null>(null)

  const handleClearCache = async () => {
    setCacheStatus('Clearing...')
    try {
      const res = await clearCache()
      setCacheStatus(res.message || 'Cache cleared successfully')
    } catch (error: any) {
      setCacheStatus('Error: ' + error.message)
    }
  }

  const handleRetrain = async () => {
    setTrainStatus('Retraining...')
    try {
      const res = await retrainModel()
      setTrainStatus(res.message || 'Model retrained successfully')
    } catch (error: any) {
      setTrainStatus('Error: ' + error.message)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-on-surface mb-2">Settings</h1>
      <p className="text-sm text-on-surface-variant mb-6">System configuration, API keys, cache controls, and model retraining.</p>
      <div className="space-y-6">
        <div className="border-b border-white/5 pb-4">
          <h2 className="text-sm font-semibold text-on-surface">API Keys</h2>
          <p className="text-xs text-on-surface-variant">Manage Groq, Neon, and Redis credentials.</p>
        </div>
        <div className="border-b border-white/5 pb-4">
          <h2 className="text-sm font-semibold text-on-surface">Cache Management</h2>
          <p className="text-xs text-on-surface-variant">Clear Redis cache (exact & semantic).</p>
          <button onClick={handleClearCache} className="mt-2 bg-error/20 text-error px-4 py-1.5 rounded text-xs border border-error/30 hover:bg-error/30 transition">
            Clear Cache
          </button>
          {cacheStatus && <p className="text-xs text-secondary mt-2">{cacheStatus}</p>}
        </div>
        <div>
          <h2 className="text-sm font-semibold text-on-surface">Model Retraining</h2>
          <p className="text-xs text-on-surface-variant">Trigger a new training job using the latest patient data.</p>
          <button onClick={handleRetrain} className="mt-2 bg-primary/20 text-primary px-4 py-1.5 rounded text-xs border border-primary/30 hover:bg-primary/30 transition">
            Retrain Model
          </button>
          {trainStatus && <p className="text-xs text-secondary mt-2">{trainStatus}</p>}
        </div>
      </div>
    </div>
  )
}