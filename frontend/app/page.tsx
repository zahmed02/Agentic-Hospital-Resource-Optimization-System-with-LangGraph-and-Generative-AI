'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getBedOccupancy, getDashboardStats, getDischargePredictions } from '@/lib/api'

type Ward = { ward: string; occupied: number; total: number }
type Prediction = { patient_id?: string; patient_name?: string; ward?: string; predicted_discharge_date?: string; confidence?: number }

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null); const [wards, setWards] = useState<Ward[]>([]); const [predictions, setPredictions] = useState<Prediction[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(false)
  const loadDashboard = async () => { setLoading(true); setError(false); try { const [s,b,p] = await Promise.all([getDashboardStats(), getBedOccupancy(), getDischargePredictions()]); setStats(s); setWards(b || []); setPredictions((p || []).slice(0, 5)) } catch { setError(true) } finally { setLoading(false) } }
  useEffect(() => { loadDashboard() }, [])
  const occupancy = Number(stats?.bed_occupancy_pct || 0)
  const metrics = [{ label:'Active patients', value:stats?.active_patients ?? '—', note:`${stats?.total_patients ?? '—'} total in registry` }, { label:'Bed occupancy', value:stats ? `${occupancy}%` : '—', note:occupancy >= 85 ? 'Capacity review needed' : 'Within operating range' }, { label:'Average length of stay', value:stats ? `${stats.avg_los_days ?? '—'} days` : '—', note:'Across active admissions' }, { label:'Discharges to plan', value:stats?.pending_discharges ?? '—', note:'Expected today' }]
  return <div>
    <div className="page-heading"><div><p className="section-label">Clinical operations</p><h1>Overview</h1><p>Monitor patient flow, bed capacity, and discharge planning across the hospital.</p></div><button onClick={loadDashboard} disabled={loading} className="action-button">{loading ? 'Updating' : 'Refresh data'}</button></div>
    {error && <div className="medical-card alert-card">Live data is temporarily unavailable. Try refreshing when the service is online.</div>}
    <div className="metric-grid">{metrics.map((item) => <div className="medical-card metric-card" key={item.label}><p>{item.label}</p><strong>{loading ? '—' : item.value}</strong><span>{item.note}</span></div>)}</div>
    <div className="dashboard-grid">
      <section className="medical-card panel"><div className="panel-header"><div><p className="section-label">Capacity</p><h2>Bed occupancy by ward</h2></div><Link href="/explorer">View patient registry</Link></div><div className="ward-list">{wards.length ? wards.map((ward) => { const percent = ward.total ? Math.round(ward.occupied / ward.total * 100) : 0; return <div className="ward-row" key={ward.ward}><div><strong>{ward.ward}</strong><span>{ward.occupied} of {ward.total} beds occupied</span></div><div className="bar-track"><div className={percent >= 85 ? 'bar-fill warning' : 'bar-fill'} style={{width:`${percent}%`}} /></div><b>{percent}%</b></div> }) : <p className="muted">No ward capacity data available.</p>}</div></section>
      <section className="medical-card panel"><div className="panel-header"><div><p className="section-label">Patient flow</p><h2>Discharge planning</h2></div><Link href="/explainability">Model insights</Link></div><div className="prediction-list">{predictions.length ? predictions.map((p, i) => <div className="prediction-row" key={`${p.patient_id}-${i}`}><div><strong>{p.patient_name || p.patient_id || 'Patient record'}</strong><span>{p.ward || 'Assigned ward'}{p.predicted_discharge_date ? ` · ${new Date(p.predicted_discharge_date).toLocaleDateString('en-US',{month:'short',day:'numeric'})}` : ''}</span></div><b>{p.confidence ? `${p.confidence}%` : 'Review'}</b></div>) : <p className="muted">No discharge predictions need review.</p>}</div></section>
    </div>
    <section className="medical-card assistant-banner"><div><p className="section-label">Clinical support</p><h2>Need a clinical answer?</h2><p>Ask the assistant to find patients, summarize flow, or explain a prediction.</p></div><Link href="/ai-agent" className="primary-button">Open assistant</Link></section>
  </div>
}
