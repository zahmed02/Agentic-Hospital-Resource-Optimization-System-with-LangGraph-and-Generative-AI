'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { FaSearch, FaFilter, FaEye, FaBrain } from 'react-icons/fa'
import { getPatients, getPatient } from '@/lib/api'

export default function ExplorerPage() {
  const [patients, setPatients] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterWard, setFilterWard] = useState('ALL WARDS')
  const [filterCondition, setFilterCondition] = useState('ANY')
  const [selectedPatient, setSelectedPatient] = useState<any>(null)

  const loadPatients = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (search) params.search = search
      if (filterWard !== 'ALL WARDS') params.ward = filterWard
      if (filterCondition !== 'ANY') params.condition = filterCondition
      const data = await getPatients(params)
      setPatients(data)
    } catch (error) {
      console.error('Failed to load patients', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPatients()
  }, [search, filterWard, filterCondition])

  const handleSelectPatient = async (id: number) => {
    try {
      const data = await getPatient(id)
      setSelectedPatient(data)
    } catch (error) {
      console.error('Failed to load patient details', error)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        {/* Filter bar */}
        <div className="glass-panel p-4 rounded-lg flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs font-medium text-outline mb-1">PATIENT ID / NAME</label>
            <div className="relative">
              <FaSearch className="absolute left-2 top-1/2 -translate-y-1/2 text-outline-variant" />
              <input
                className="w-full bg-surface-dim border-b border-outline-variant focus:border-secondary focus:ring-0 text-on-surface pl-8 py-2 text-sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div className="w-40">
            <label className="block text-xs font-medium text-outline mb-1">WARD</label>
            <select className="w-full bg-surface-dim border-b border-outline-variant focus:border-secondary focus:ring-0 text-on-surface py-2 text-sm" value={filterWard} onChange={(e) => setFilterWard(e.target.value)}>
              <option>ALL WARDS</option>
              <option>ICU</option>
              <option>CARDIOLOGY</option>
              <option>ORTHOPEDICS</option>
              <option>INTERNAL MEDICINE</option>
            </select>
          </div>
          <div className="w-40">
            <label className="block text-xs font-medium text-outline mb-1">CONDITION</label>
            <select className="w-full bg-surface-dim border-b border-outline-variant focus:border-secondary focus:ring-0 text-on-surface py-2 text-sm" value={filterCondition} onChange={(e) => setFilterCondition(e.target.value)}>
              <option>ANY</option>
              <option>CRITICAL</option>
              <option>STABLE</option>
            </select>
          </div>
          <button onClick={loadPatients} className="bg-surface-variant hover:bg-surface-bright text-on-surface px-4 py-2 border border-white/10 rounded flex items-center gap-2 text-sm">
            <FaFilter /> APPLY
          </button>
        </div>

        {/* Patient Table */}
        <div className="glass-panel rounded-lg overflow-hidden">
          <div className="p-3 border-b border-white/10 flex justify-between items-center bg-surface-container-high/50">
            <span className="text-xs font-medium text-outline">ACTIVE PATIENT REGISTRY</span>
            <span className="text-xs text-secondary">{patients.length} RECORDS</span>
          </div>
          {loading ? (
            <div className="p-10 text-center text-outline">Loading...</div>
          ) : patients.length === 0 ? (
            <div className="p-10 text-center text-outline">No patients found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-surface-container-lowest/50 text-left text-xs text-outline-variant">
                  <tr>
                    <th className="p-3">ID</th><th className="p-3">NAME</th><th className="p-3">WARD</th>
                    <th className="p-3">CONDITION</th><th className="p-3">STATUS</th><th className="p-3 text-right">ACTIONS</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-xs">
                  {patients.map((p) => (
                    <tr key={p.id} className="border-b border-white/5 hover:bg-surface-bright/30 transition">
                      <td className="p-3 text-secondary">{p.patient_id}</td>
                      <td className="p-3">{p.name}</td>
                      <td className="p-3">{p.ward || '—'}</td>
                      <td className="p-3">{p.condition}</td>
                      <td className="p-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] ${p.is_active ? 'bg-secondary/20 text-secondary border border-secondary/30' : 'bg-outline/20 text-outline border border-outline/30'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${p.is_active ? 'bg-secondary animate-pulse' : 'bg-outline'}`}></span>
                          {p.is_active ? 'Active' : 'Discharged'}
                        </span>
                      </td>
                      <td className="p-3 text-right flex justify-end gap-2">
                        <button onClick={() => handleSelectPatient(p.id)} className="text-primary hover:bg-primary/10 p-1 rounded">
                          <FaEye />
                        </button>
<Link href={`/explainability/${p.id}`} className="text-secondary hover:bg-secondary/10 p-1 rounded">
  <FaBrain />
</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Patient Detail Sidebar */}
      <div className="glass-panel rounded-lg p-4 border border-primary/30 glow-active">
        {selectedPatient ? (
          <>
            <div className="h-1 w-full bg-gradient-to-r from-error via-secondary to-primary rounded-t"></div>
            <div className="flex items-start gap-4 mt-3">
              <div className="w-16 h-16 rounded-full bg-surface-variant flex items-center justify-center text-3xl">👤</div>
              <div>
                <h3 className="font-semibold text-on-surface">{selectedPatient.name} <span className="text-xs text-outline">#{selectedPatient.patient_id}</span></h3>
                <p className="text-xs text-outline">Age: {selectedPatient.age} | {selectedPatient.gender}</p>
                <p className="text-xs text-outline">Condition: {selectedPatient.condition}</p>
                <span className="inline-block mt-1 px-2 py-0.5 bg-error/20 text-error text-[10px] rounded border border-error/30">
                  {selectedPatient.is_active ? 'Active' : 'Discharged'}
                </span>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex justify-between items-center">
                <span className="text-xs text-secondary flex items-center gap-1"><FaBrain /> AI PREDICTED LOS</span>
                <span className="text-xs text-outline">CONF: {selectedPatient.prediction?.confidence || 'N/A'}%</span>
              </div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-on-surface">
                  {selectedPatient.prediction?.predicted_discharge_date ? 
                    Math.ceil((new Date(selectedPatient.prediction.predicted_discharge_date).getTime() - new Date(selectedPatient.admission_date).getTime()) / (1000*60*60*24)) 
                    : '—'}
                </span>
                <span className="text-xs text-outline pb-1">DAYS</span>
              </div>
              <div className="h-16 w-full bg-surface-dim rounded border border-white/5 flex items-end p-1 gap-1 mt-2">
                <div className="w-1/4 bg-error/40 border-t border-error h-[80%]"></div>
                <div className="w-1/4 bg-error/30 border-t border-error/70 h-[60%]"></div>
                <div className="w-1/4 bg-secondary/30 border-t border-secondary/70 h-[40%]"></div>
                <div className="w-1/4 bg-outline/20 border-t border-outline/50 h-[20%]"></div>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button className="flex-1 bg-primary/10 text-primary border border-primary/30 text-xs py-2 rounded hover:bg-primary/20">FULL CHART</button>
              <button className="flex-1 bg-surface-variant text-on-surface border border-white/10 text-xs py-2 rounded hover:bg-surface-bright">ORDER SETS</button>
            </div>
          </>
        ) : (
          <div className="text-center text-outline py-10">Select a patient to view details</div>
        )}
      </div>
    </div>
  )
}