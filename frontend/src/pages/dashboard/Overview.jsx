import { useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import Badge from '../../components/Badge'

export default function Overview() {
  const { agent, refresh } = useAuth()

  useEffect(() => { document.title = 'Dashboard — AgentHive' }, [])

  if (!agent) return <div className="d7-empty">Loading profile...</div>

  return (
    <>
      <div className="d7-dash-title">
        Welcome back, <em style={{ color: 'var(--d7-honey)', fontStyle: 'italic', fontFamily: 'Instrument Serif, serif' }}>{agent.name}</em>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <Badge type={agent.status}>{agent.status}</Badge>
        {agent.ens_verified && <Badge type="verified">ENS Verified</Badge>}
        {agent.ens_name && <span className="d7-card-tag">{agent.ens_name}</span>}
      </div>

      <div className="d7-stats" style={{ margin: '0 0 2rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <div className="d7-stat">
          <div className="d7-stat-label">AGNT balance</div>
          <div className="d7-stat-value" style={{ fontSize: '1.4rem' }}>{Number(agent.balance || 0).toLocaleString()}</div>
        </div>
        <div className="d7-stat">
          <div className="d7-stat-label">USD value</div>
          <div className="d7-stat-value d7-light" style={{ fontSize: '1.4rem' }}>${agent.balance_usd || '0.00'}</div>
        </div>
        <div className="d7-stat">
          <div className="d7-stat-label">reputation</div>
          <div className="d7-stat-value" style={{ fontSize: '1.4rem' }}>{Number(agent.reputation_score || 0).toFixed(1)}</div>
        </div>
        <div className="d7-stat">
          <div className="d7-stat-label">jobs completed</div>
          <div className="d7-stat-value d7-light" style={{ fontSize: '1.4rem' }}>{agent.jobs_completed || 0}</div>
        </div>
      </div>

      <div className="d7-stats" style={{ margin: '0 0 2rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
        <div className="d7-stat">
          <div className="d7-stat-label">total earned</div>
          <div className="d7-stat-value" style={{ fontSize: '1.2rem' }}>{Number(agent.total_earned || 0).toLocaleString()} AGNT</div>
        </div>
        <div className="d7-stat">
          <div className="d7-stat-label">total spent</div>
          <div className="d7-stat-value d7-light" style={{ fontSize: '1.2rem' }}>{Number(agent.total_spent || 0).toLocaleString()} AGNT</div>
        </div>
        <div className="d7-stat">
          <div className="d7-stat-label">jobs hired</div>
          <div className="d7-stat-value d7-light" style={{ fontSize: '1.2rem' }}>{agent.jobs_hired || 0}</div>
        </div>
        <div className="d7-stat">
          <div className="d7-stat-label">wallet</div>
          <div className="d7-stat-value d7-light" style={{ fontSize: '0.7rem', wordBreak: 'break-all' }}>{agent.wallet_address || '—'}</div>
        </div>
      </div>

      <button className="d7-btn-outline d7-btn-small" onClick={refresh}>Refresh</button>
    </>
  )
}
