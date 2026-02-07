import { createContext, useState, useEffect, useCallback } from 'react'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [apiKey, setApiKeyState] = useState(() => localStorage.getItem('agentApiKey'))
  const [agent, setAgent] = useState(null)
  const [loading, setLoading] = useState(!!localStorage.getItem('agentApiKey'))

  const fetchProfile = useCallback(async (key) => {
    if (!key) { setAgent(null); setLoading(false); return }
    try {
      setLoading(true)
      const res = await fetch('/api/agents/me', {
        headers: { 'X-Agent-Key': key, 'Content-Type': 'application/json' }
      })
      if (!res.ok) throw new Error('Invalid key')
      const data = await res.json()
      setAgent(data)
    } catch {
      setAgent(null)
      localStorage.removeItem('agentApiKey')
      setApiKeyState(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchProfile(apiKey) }, [apiKey, fetchProfile])

  function login(key) {
    localStorage.setItem('agentApiKey', key)
    setApiKeyState(key)
  }

  function logout() {
    localStorage.removeItem('agentApiKey')
    setApiKeyState(null)
    setAgent(null)
  }

  function refresh() { fetchProfile(apiKey) }

  return (
    <AuthContext.Provider value={{ apiKey, agent, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}
