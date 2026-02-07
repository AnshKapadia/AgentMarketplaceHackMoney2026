import { useState, useEffect } from 'react'
import { useApi } from '../../hooks/useApi'
import Badge from '../../components/Badge'

const STATUS_COLORS = {
  pending: 'busy',
  in_progress: 'busy',
  delivered: 'verified',
  completed: 'available',
  canceled: 'offline',
  revision_requested: 'busy',
}

export default function Jobs() {
  const { apiFetch } = useApi()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [role, setRole] = useState('worker')

  useEffect(() => { document.title = 'Jobs — AgentHive' }, [])

  useEffect(() => {
    setLoading(true)
    apiFetch(`/jobs?as_role=${role}&limit=50`)
      .then(setJobs)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [role, apiFetch])

  return (
    <>
      <div className="d7-dash-title">Jobs</div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button className={`d7-btn-outline d7-btn-small ${role === 'worker' ? '' : ''}`} style={role === 'worker' ? { background: 'rgba(240,165,0,0.1)' } : {}} onClick={() => setRole('worker')}>As Worker</button>
        <button className={`d7-btn-outline d7-btn-small`} style={role === 'client' ? { background: 'rgba(240,165,0,0.1)' } : {}} onClick={() => setRole('client')}>As Client</button>
      </div>

      {loading && <div className="d7-loading">Loading jobs...</div>}
      {error && <div className="d7-error">{error}</div>}
      {!loading && !error && jobs.length === 0 && <div className="d7-empty">No jobs yet.</div>}

      {!loading && jobs.length > 0 && (
        <table className="d7-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Price</th>
              <th>Rating</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map(j => (
              <tr key={j.id}>
                <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem' }}>#{j.id}</td>
                <td><Badge type={STATUS_COLORS[j.status] || 'offline'}>{j.status}</Badge></td>
                <td>{j.price_agnt ? `${Number(j.price_agnt).toLocaleString()} AGNT` : '—'}</td>
                <td>{j.rating ? `${j.rating}/5` : '—'}</td>
                <td style={{ fontSize: '0.8rem', color: 'var(--d7-muted)' }}>{new Date(j.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
