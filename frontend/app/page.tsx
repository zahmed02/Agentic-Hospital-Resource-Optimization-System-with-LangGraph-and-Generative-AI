'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Activity, ArrowUpRight, BedDouble, BrainCircuit, CalendarClock, CircleAlert, Clock3, RefreshCw, UserRound, UsersRound } from 'lucide-react'
import { getBedOccupancy, getDashboardStats, getDischargePredictions } from '@/lib/api'

type Ward = { ward: string; occupied: number; total: number }
type Prediction = { patient_id?: string; patient_name?: string; ward?: string; predicted_discharge_date?: string; confidence?: number }

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null)
  const [wards, setWards] = useState<Ward[]>([])
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const loadDashboard = async () => {
    setLoading(true); setError(false)
    try {
      const [statsRes, bedsRes, predictionsRes] = await Promise.all([getDashboardStats(), getBedOccupancy(), getDischargePredictions()])
      setStats(statsRes); setWards(bedsRes || []); setPredictions((predictionsRes || []).slice(0, 5))
    } catch { setError(true) } finally { setLoading(false) }
  }
  useEffect(() => { loadDashboard() }, [])

  const occupancy = Number(stats?.bed_occupancy_pct || 0)
  return <div className="flex flex-col gap-8">
    <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
      <div><div className="mb-3 flex items-center gap-2 text-xs font-medium text-teal-400"><Activity aria-hidden="true" /> LIVE OPERATIONS VIEW <span className="size-1.5 rounded-full bg-emerald-400" /></div><h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Good morning, Jordan</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">A clear view of patient flow, capacity, and the decisions that need attention today.</p></div>
      <button onClick={loadDashboard} className="inline-flex items-center justify-center gap-2 self-start rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-teal-500/50 hover:text-teal-300 md:self-auto" disabled={loading}><RefreshCw aria-hidden="true" className={loading ? 'animate-spin' : ''} /> Refresh data</button>
    </section>
    {error && <div role="alert" className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200"><CircleAlert aria-hidden="true" /> Live data is temporarily unavailable. Try refreshing when the service is online.</div>}
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {[{label:'Active patients', value:stats?.active_patients ?? '—', meta:`${stats?.total_patients ?? '—'} total in registry`, icon:UsersRound, tone:'teal'}, {label:'Bed occupancy', value:stats ? `${occupancy}%` : '—', meta:occupancy >= 85 ? 'Capacity review needed' : 'Within operating range', icon:BedDouble, tone:'blue'}, {label:'Average length of stay', value:stats ? `${stats.avg_los_days ?? '—'} days` : '—', meta:'Across active admissions', icon:Clock3, tone:'violet'}, {label:'Discharges to plan', value:stats?.pending_discharges ?? '—', meta:'Expected today', icon:CalendarClock, tone:'amber'}].map((item) => { const Icon = item.icon; return <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-2xl shadow-slate-950/20"><div className="flex items-start justify-between"><p className="text-sm text-slate-400">{item.label}</p><span className={`rounded-lg p-2 ${item.tone === 'teal' ? 'bg-teal-500/10 text-teal-300' : item.tone === 'blue' ? 'bg-blue-500/10 text-blue-300' : item.tone === 'violet' ? 'bg-violet-500/10 text-violet-300' : 'bg-amber-500/10 text-amber-300'}`}><Icon aria-hidden="true" /></span></div><p className="mt-4 text-3xl font-semibold tracking-tight text-white">{loading ? '…' : item.value}</p><p className="mt-1 text-xs text-slate-500">{item.meta}</p></div> })}
    </section>
    <section className="grid gap-5 xl:grid-cols-[1.45fr_1fr]">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6"><div className="flex items-start justify-between"><div><h2 className="font-semibold text-white">Capacity by ward</h2><p className="mt-1 text-sm text-slate-500">Current occupied beds across active units</p></div><Link href="/explorer" className="inline-flex items-center gap-1 text-xs font-medium text-teal-400 hover:text-teal-300">View registry <ArrowUpRight aria-hidden="true" /></Link></div><div className="mt-7 flex min-h-60 items-end gap-3 border-b border-slate-800 pb-0 sm:gap-5">{wards.length ? wards.map((ward) => { const percent = ward.total ? Math.round(ward.occupied / ward.total * 100) : 0; return <div key={ward.ward} className="flex min-w-0 flex-1 flex-col items-center gap-2"><span className="text-xs font-medium text-slate-300">{percent}%</span><div className="flex h-44 w-full items-end rounded-t-lg bg-slate-800/60"><div className={`w-full rounded-t-lg bg-gradient-to-t ${percent >= 85 ? 'from-amber-600 to-amber-400' : 'from-teal-700 to-teal-400'}`} style={{height:`${Math.max(percent, 8)}%`}} /></div><span className="truncate pb-3 text-[11px] text-slate-500">{ward.ward}</span></div> }) : <div className="flex w-full items-center justify-center pb-6 text-sm text-slate-500">No ward capacity data available</div>}</div></div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 sm:p-6"><div className="flex items-start justify-between"><div><h2 className="font-semibold text-white">Discharge planning</h2><p className="mt-1 text-sm text-slate-500">AI-assisted readiness signals</p></div><span className="rounded-lg bg-violet-500/10 p-2 text-violet-300"><BrainCircuit aria-hidden="true" /></span></div><div className="mt-6 flex flex-col gap-3">{predictions.length ? predictions.map((prediction, index) => <div key={`${prediction.patient_id}-${index}`} className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-950/50 p-3"><div className="flex size-9 items-center justify-center rounded-full bg-slate-800 text-slate-400"><UserRound aria-hidden="true" /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-slate-200">{prediction.patient_name || prediction.patient_id || 'Patient record'}</p><p className="text-xs text-slate-500">{prediction.ward || 'Assigned ward'}{prediction.predicted_discharge_date ? ` · ${new Date(prediction.predicted_discharge_date).toLocaleDateString('en-US', {month:'short', day:'numeric'})}` : ''}</p></div><span className="text-xs font-medium text-teal-400">{prediction.confidence ? `${prediction.confidence}%` : 'Review'}</span></div>) : <div className="rounded-xl border border-dashed border-slate-700 px-4 py-8 text-center text-sm text-slate-500">No discharge predictions need review.</div>}</div><Link href="/explainability" className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-teal-400 hover:text-teal-300">Review model insights <ArrowUpRight aria-hidden="true" /></Link></div>
    </section>
    <section className="rounded-2xl border border-teal-500/20 bg-gradient-to-r from-teal-500/10 to-slate-900/60 p-5 sm:p-6"><div className="flex flex-col justify-between gap-4 md:flex-row md:items-center"><div className="flex items-start gap-4"><div className="rounded-xl bg-teal-500/15 p-3 text-teal-300"><BrainCircuit aria-hidden="true" /></div><div><h2 className="font-semibold text-white">Need a clinical answer?</h2><p className="mt-1 text-sm text-slate-400">Ask the assistant to find patients, summarize flow, or explain a prediction.</p></div></div><Link href="/ai-agent" className="inline-flex items-center justify-center gap-2 rounded-lg bg-teal-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-teal-400">Open assistant <ArrowUpRight aria-hidden="true" /></Link></div></section>
  </div>
}
