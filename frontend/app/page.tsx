'use client'

import { useState, useEffect } from 'react'
import { FaHeartbeat, FaBed, FaClock, FaSignOutAlt, FaBrain, FaArrowRight } from 'react-icons/fa'
import KpiCard from '@/components/KpiCard'
import ActivityItem from '@/components/ActivityItem'
import { getDashboardStats, getBedOccupancy, getDischargePredictions } from '@/lib/api'

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null)
  const [bedData, setBedData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, bedRes] = await Promise.all([
          getDashboardStats(),
          getBedOccupancy(),
        ])
        setStats(statsRes)
        setBedData(bedRes)
      } catch (error) {
        console.error('Failed to load dashboard data', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) return <div className="text-center py-10 text-on-surface-variant">Loading dashboard...</div>

  return (
    <>
      {/* Query Input – same as before, but we'll keep it for now */}
      <div className="mb-8">
        <div className="widget-card rounded-xl p-5 relative glow-active overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent pointer-events-none"></div>
          <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <FaBrain className="text-secondary text-2xl shrink-0" />
            <input
              className="flex-1 w-full bg-transparent border-0 border-b border-outline-variant focus:border-secondary focus:ring-0 text-on-surface font-body-lg text-body-lg py-2 placeholder-outline transition-colors"
              placeholder="Query AI Agent (e.g. 'Show patients with high risk of readmission')"
              // we can add a submit handler later
            />
            <button className="bg-primary/10 border border-primary text-primary px-6 py-2 rounded-lg font-label-caps text-label-caps hover:bg-primary/20 transition-colors flex items-center gap-2 whitespace-nowrap">
              EXECUTE <FaArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KpiCard title="Total Patients" value={stats?.total_patients || 0} change={`Active: ${stats?.active_patients || 0}`} changeType="positive" icon={<FaHeartbeat />} />
        <KpiCard title="Bed Occupancy" value={`${stats?.bed_occupancy_pct || 0}%`} progress={stats?.bed_occupancy_pct || 0} icon={<FaBed />} />
        <KpiCard title="Avg LOS (Days)" value={stats?.avg_los_days || 0} change="Real data" changeType="negative" icon={<FaClock />} />
        <KpiCard title="Pending Discharges" value={stats?.pending_discharges || 0} change="Due today" changeType="warning" icon={<FaSignOutAlt />} className="border-error/30" />
      </div>

      {/* Chart & Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 widget-card rounded-xl p-5">
          <div className="flex flex-wrap justify-between items-center mb-4 border-b border-white/5 pb-3">
            <h2 className="font-label-caps text-label-caps text-on-surface">Live Ward Occupancy</h2>
            <div className="flex gap-4 text-xs">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-secondary"></span> Occupied</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-outline"></span> Free</span>
            </div>
          </div>
          <div className="flex items-end justify-between gap-2 h-64">
            {bedData.length > 0 ? bedData.map((ward, i) => {
              const occupiedPct = ward.total > 0 ? (ward.occupied / ward.total * 100) : 0
              const isCritical = occupiedPct >= 85
              return (
                <div key={i} className="flex flex-col items-center gap-1 flex-1">
                  <div className="w-full chart-bar-stable rounded-t-sm transition-all hover:opacity-80" style={{ height: `${Math.max(occupiedPct, 10)}%` }}>
                    <div className="text-center text-[10px] font-data-mono text-on-surface pt-1">{Math.round(occupiedPct)}%</div>
                  </div>
                  <span className={`text-[10px] font-data-mono ${isCritical ? 'text-error font-bold' : 'text-outline'}`}>{ward.ward}</span>
                </div>
              )
            }) : <p className="text-center w-full text-outline">No bed data available</p>}
          </div>
        </div>

        <div className="widget-card rounded-xl p-5">
          <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-3">
            <h2 className="font-label-caps text-label-caps text-on-surface">Recent Predictions</h2>
            <span className="text-outline text-sm">⋯</span>
          </div>
          <div className="space-y-4 max-h-72 overflow-y-auto pr-1">
            {/* Fetch recent predictions from API */}
            { /* We'll use a separate useEffect for predictions */}
          </div>
        </div>
      </div>
    </>
  )
}