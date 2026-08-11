'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { FaArrowLeft, FaSync, FaBrain } from 'react-icons/fa'
import { getExplanation } from '@/lib/api'

export default function ExplainabilityPage() {
  const searchParams = useSearchParams()
  const patientId = searchParams.get('id')
  const [explanation, setExplanation] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadExplanation = async (id: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getExplanation(id)
      setExplanation(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load explanation')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (patientId) {
      loadExplanation(Number(patientId))
    }
  }, [patientId])

  if (!patientId) {
    return (
      <div className="text-center py-20 text-on-surface-variant">
        <p className="text-lg">No patient selected</p>
        <Link href="/explorer" className="text-primary hover:underline">Go to Explorer</Link>
      </div>
    )
  }

  if (loading) return <div className="text-center py-10 text-on-surface-variant">Loading explanation...</div>
  if (error) return <div className="text-center py-10 text-error">{error}</div>
  if (!explanation) return null

  const { patient_id, predicted_los_days, feature_values, feature_contributions, intercept } = explanation

  return (
    <div>
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <Link href="/explorer" className="flex items-center gap-1 text-secondary hover:text-primary text-sm">
            <FaArrowLeft /> Back to Explorer
          </Link>
          <h1 className="text-2xl font-bold text-on-surface mt-1">{patient_id} <span className="text-xs bg-surface-variant px-2 py-0.5 rounded text-outline">PREDICTION ANALYSIS</span></h1>
        </div>
        <button onClick={() => loadExplanation(Number(patientId))} className="bg-surface-variant hover:bg-surface-bright text-on-surface border border-outline-variant px-4 py-2 rounded text-xs flex items-center gap-2">
          <FaSync /> RE-RUN EXPLANATION
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-5 rounded-lg flex flex-col justify-between">
          <div>
            <h2 className="text-xs uppercase tracking-wider text-outline">LOS Forecast</h2>
            <div className="border-b border-white/5 py-3">
              <p className="text-sm text-on-surface-variant">Intercept (Baseline)</p>
              <p className="text-2xl font-bold text-on-surface">{intercept} <span className="text-sm text-outline">days</span></p>
            </div>
            <div className="py-3">
              <p className="text-sm text-secondary flex items-center gap-1"><FaBrain /> AI Adjusted</p>
              <p className="text-2xl font-bold text-error">{predicted_los_days} <span className="text-sm text-outline">days</span></p>
              <div className="mt-1 text-xs bg-error/10 text-error px-2 py-1 rounded inline-block">+{(predicted_los_days - intercept).toFixed(1)} days deviation</div>
            </div>
          </div>
          {/* Confidence not provided by current API, we can add later */}
        </div>

        <div className="md:col-span-2 glass-card p-5 rounded-lg">
          <div className="flex justify-between items-center border-b border-white/5 pb-2">
            <h2 className="text-xs uppercase tracking-wider text-outline">Feature Weights</h2>
            <div className="flex gap-3 text-xs">
              <span className="flex items-center gap-1 text-error"><span className="w-2 h-2 rounded-full bg-error"></span> Increases LOS</span>
              <span className="flex items-center gap-1 text-primary"><span className="w-2 h-2 rounded-full bg-primary"></span> Decreases LOS</span>
            </div>
          </div>
          <div className="space-y-3 mt-3">
            {feature_contributions.map((f: any, idx: number) => {
              const isPositive = f.contribution > 0
              const width = Math.min(Math.abs(f.contribution) * 10, 80)
              return (
                <div key={idx} className="flex items-center gap-2">
                  <span className="w-1/3 text-right text-xs text-on-surface truncate">{f.feature}</span>
                  <div className="w-2/3 bg-surface-container-high h-5 rounded-r flex items-center">
                    <div className={`h-full ${isPositive ? 'bg-error/80' : 'bg-primary/80'} rounded-r flex items-center px-2 text-xs text-on-${isPositive ? 'error' : 'primary'}`} style={{ width: `${width}%` }}>
                      {f.contribution > 0 ? '+' : ''}{f.contribution.toFixed(2)}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          <div className="text-center text-[10px] text-outline mt-4 border-t border-white/5 pt-2">X‑AXIS: Impact on Baseline (days)</div>
        </div>
      </div>

      <div className="glass-card p-4 rounded-lg mt-6 flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl text-secondary">📊</span>
          <div>
            <p className="text-xs text-outline">MODEL CONTEXT</p>
            <p className="text-sm text-on-surface">Random Forest ensemble (v2.4). Local surrogate model applied.</p>
          </div>
        </div>
        <div className="flex gap-4">
          <div className="bg-surface-container-high px-4 py-2 rounded border border-white/5 text-center">
            <p className="text-[10px] text-outline">FEATURES</p>
            <p className="text-sm font-bold text-on-surface">{feature_contributions.length}</p>
          </div>
          <div className="bg-surface-container-high px-4 py-2 rounded border border-white/5 text-center">
            <p className="text-[10px] text-outline">TIME</p>
            <p className="text-sm font-bold text-on-surface">~1.2s</p>
          </div>
        </div>
      </div>
    </div>
  )
}