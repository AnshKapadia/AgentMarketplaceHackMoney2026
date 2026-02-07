import { useCallback } from 'react'

const BASE = '/api'

export function useApi() {
  const apiKey = localStorage.getItem('agentApiKey')

  const apiFetch = useCallback(async (path, options = {}) => {
    const headers = { 'Content-Type': 'application/json', ...options.headers }
    const key = localStorage.getItem('agentApiKey')
    if (key) headers['X-Agent-Key'] = key
    const res = await fetch(`${BASE}${path}`, { ...options, headers })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      const msg = body?.detail?.message || body?.detail || res.statusText
      throw new Error(msg)
    }
    return res.json()
  }, [])

  return { apiFetch, apiKey }
}
