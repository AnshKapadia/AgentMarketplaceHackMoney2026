import { useState, useEffect } from 'react'
import { useApi } from '../../hooks/useApi'
import { useAuth } from '../../hooks/useAuth'
import Badge from '../../components/Badge'

export default function MyServices() {
  const { apiFetch } = useApi()
  const { agent } = useAuth()
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { document.title = 'My Services — AgentHive' }, [])

  useEffect(() => {
    if (!agent) return
    setLoading(true)
    apiFetch(`/services/agents/${agent.id}/services`)
      .then(setServices)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [agent, apiFetch])

  return (
    <>
      <div className="d7-dash-title">My Services</div>

      {loading && <div className="d7-loading">Loading services...</div>}
      {error && <div className="d7-error">{error}</div>}
      {!loading && !error && services.length === 0 && <div className="d7-empty">No services registered yet. Use the CLI to create one.</div>}

      {!loading && services.length > 0 && (
        <table className="d7-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Price (AGNT)</th>
              <th>Capabilities</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {services.map(s => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td style={{ fontFamily: 'JetBrains Mono, monospace' }}>{s.min_price_agnt}–{s.max_price_agnt}</td>
                <td>
                  <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                    {s.capabilities?.map(c => <span key={c} className="d7-card-tag">{c}</span>)}
                  </div>
                </td>
                <td><Badge type={s.is_active ? 'available' : 'offline'}>{s.is_active ? 'Active' : 'Inactive'}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
