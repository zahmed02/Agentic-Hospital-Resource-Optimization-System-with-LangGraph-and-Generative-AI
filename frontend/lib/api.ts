const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ---------- Agent ----------
export async function queryAgent(query: string) {
  const res = await fetch(`${BASE_URL}/agent/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) throw new Error('Agent query failed')
  return res.json()
}

// ---------- Explainability ----------
export async function getExplanation(patientId: number) {
  const res = await fetch(`${BASE_URL}/explain/predict/${patientId}`)
  if (!res.ok) throw new Error('Explanation fetch failed')
  return res.json()
}

// ---------- Dashboard ----------
export async function getDashboardStats() {
  const res = await fetch(`${BASE_URL}/api/dashboard/stats`)
  if (!res.ok) throw new Error('Failed to fetch dashboard stats')
  return res.json()
}

// ---------- Patients ----------
export async function getPatients(params?: { search?: string; ward?: string; condition?: string }) {
  const qs = new URLSearchParams(params as any).toString()
  const res = await fetch(`${BASE_URL}/api/patients?${qs}`)
  if (!res.ok) throw new Error('Failed to fetch patients')
  return res.json()
}

export async function getPatient(id: number) {
  const res = await fetch(`${BASE_URL}/api/patients/${id}`)
  if (!res.ok) throw new Error('Failed to fetch patient')
  return res.json()
}

// ---------- Beds ----------
export async function getBedOccupancy() {
  const res = await fetch(`${BASE_URL}/api/beds/occupancy`)
  if (!res.ok) throw new Error('Failed to fetch bed occupancy')
  return res.json()
}

// ---------- Admissions ----------
export async function getAdmissions() {
  const res = await fetch(`${BASE_URL}/api/admissions`)
  if (!res.ok) throw new Error('Failed to fetch admissions')
  return res.json()
}

// ---------- Discharge Predictions ----------
export async function getDischargePredictions() {
  const res = await fetch(`${BASE_URL}/api/discharge-predictions`)
  if (!res.ok) throw new Error('Failed to fetch predictions')
  return res.json()
}

// ---------- Cache ----------
export async function clearCache() {
  const res = await fetch(`${BASE_URL}/api/cache/clear`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to clear cache')
  return res.json()
}

// ---------- Model Retrain ----------
export async function retrainModel() {
  const res = await fetch(`${BASE_URL}/api/model/retrain`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to retrain model')
  return res.json()
}