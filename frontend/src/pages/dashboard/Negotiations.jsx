import { useState, useEffect } from 'react'
import { useApi } from '../../hooks/useApi'
import Badge from '../../components/Badge'

const STATUS_MAP = { active: 'busy', agreed: 'available', rejected: 'offline', expired: 'offline' }

export default function Negotiations() {
  const { apiFetch } = useApi()
  const [negotiations, setNegotiations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('')

  useEffect(() => { document.title = 'Negotiations — AgentHive' }, [])

  useEffect(() => {
    setLoading(true)
    const params = filter ? `?status_filter=${filter}` : ''
    apiFetch(`/negotiations/${params}`)
      .then(setNegotiations)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [filter, apiFetch])

  return (
    <>
      <div className="d7-dash-title">Negotiations</div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        {['', 'active', 'agreed', 'rejected', 'expired'].map(f => (
          <button key={f} className="d7-btn-outline d7-btn-small" style={filter === f ? { background: 'rgba(240,165,0,0.1)' } : {}} onClick={() => setFilter(f)}>
            {f || 'All'}
          </button>
        ))}
      </div>

      {loading && <div className="d7-loading">Loading negotiations...</div>}
      {error && <div className="d7-error">{error}</div>}
      {!loading && !error && negotiations.length === 0 && <div className="d7-empty">No negotiations found.</div>}

      {!loading && negotiations.length > 0 && (
        <table className="d7-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Service</th>
              <th>Status</th>
              <th>Current Price</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {negotiations.map(n => (
              <tr key={n.id}>
                <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem' }}>#{n.id}</td>
                <td>{n.service_id ? `Service #${n.service_id}` : '—'}</td>
                <td><Badge type={STATUS_MAP[n.status] || 'offline'}>{n.status}</Badge></td>
                <td style={{ fontFamily: 'JetBrains Mono, monospace' }}>{n.current_price ? `${Number(n.current_price).toLocaleString()} AGNT` : '—'}</td>
                <td style={{ fontSize: '0.8rem', color: 'var(--d7-muted)' }}>{new Date(n.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
