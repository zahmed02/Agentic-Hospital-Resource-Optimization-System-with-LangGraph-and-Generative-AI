/**
 * Generates (and persists) a stable session id for the AI Agent chat.
 * Backed by sessionStorage so it survives a page refresh but resets per
 * browser tab/window — matching the lifetime of the in-memory LangGraph
 * checkpointer on the backend (which also resets on server restart).
 */

const STORAGE_KEY = 'vitalos_session_id'

function generateId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  // Fallback for environments without crypto.randomUUID
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') {
    // SSR guard — real id is assigned client-side on mount
    return 'ssr'
  }
  const existing = window.sessionStorage.getItem(STORAGE_KEY)
  if (existing) return existing
  const id = generateId()
  window.sessionStorage.setItem(STORAGE_KEY, id)
  return id
}

export function resetSessionId(): string {
  const id = generateId()
  if (typeof window !== 'undefined') {
    window.sessionStorage.setItem(STORAGE_KEY, id)
  }
  return id
}
