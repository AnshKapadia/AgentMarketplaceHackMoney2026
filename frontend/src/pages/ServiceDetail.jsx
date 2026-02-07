import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import Badge from '../components/Badge'

export default function ServiceDetail() {
  const { id } = useParams()
  const { apiFetch } = useApi()
  const [service, setService] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    apiFetch(`/services/${id}`)
      .then(s => { setService(s); document.title = `${s.name} — AgentHive` })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id, apiFetch])

  if (loading) return <div className="d7-page"><div className="d7-loading">Loading service...</div></div>
  if (error) return <div className="d7-page"><div className="d7-page-body"><div className="d7-error">{error}</div></div></div>
  if (!service) return <div className="d7-page"><div className="d7-page-body"><div className="d7-empty">Service not found.</div></div></div>

  return (
    <div className="d7-page">
      <div className="d7-page-body">
        <div className="d7-detail">
          <div className="d7-detail-header">
            <div>
              <div className="d7-detail-title">{service.name}</div>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                <Badge type={service.is_active ? 'available' : 'offline'}>{service.is_active ? 'Active' : 'Inactive'}</Badge>
                {service.output_type && <span className="d7-card-tag">{service.output_type}</span>}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="d7-stat-value" style={{ fontSize: '1.4rem' }}>{service.min_price_agnt}–{service.max_price_agnt}</div>
              <div className="d7-stat-label">AGNT Price Range</div>
              {service.price_range_usd && <div style={{ color: 'var(--d7-muted)', fontSize: '0.8rem', marginTop: '0.3rem' }}>{service.price_range_usd}</div>}
            </div>
          </div>

          <div className="d7-detail-section">
            <div className="d7-detail-label">Description</div>
            <div className="d7-detail-text">{service.description || 'No description.'}</div>
          </div>

          {service.capabilities?.length > 0 && (
            <div className="d7-detail-section">
              <div className="d7-detail-label">Capabilities</div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {service.capabilities.map(c => <span key={c} className="d7-card-tag">{c}</span>)}
              </div>
            </div>
          )}

          <div className="d7-detail-section">
            <div className="d7-detail-label">Agent</div>
            <Link to={`/agents/${service.agent_id}`} className="d7-card" style={{ textDecoration: 'none', display: 'inline-block' }}>
              <div className="d7-card-title">{service.agent_name || `Agent #${service.agent_id}`}</div>
              <div className="d7-card-desc">View full agent profile &rarr;</div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
