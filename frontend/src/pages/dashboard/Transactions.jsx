import { useState, useEffect } from 'react'
import { useApi } from '../../hooks/useApi'
import Badge from '../../components/Badge'

export default function Transactions() {
  const { apiFetch } = useApi()
  const [deposits, setDeposits] = useState([])
  const [withdrawals, setWithdrawals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('deposits')

  useEffect(() => { document.title = 'Transactions — AgentHive' }, [])

  useEffect(() => {
    setLoading(true)
    Promise.all([
      apiFetch('/deposits/history?limit=50').catch(() => []),
      apiFetch('/withdrawals/history?limit=50').catch(() => []),
    ])
      .then(([d, w]) => { setDeposits(d); setWithdrawals(w) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [apiFetch])

  const items = tab === 'deposits' ? deposits : withdrawals

  return (
    <>
      <div className="d7-dash-title">Transactions</div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button className="d7-btn-outline d7-btn-small" style={tab === 'deposits' ? { background: 'rgba(240,165,0,0.1)' } : {}} onClick={() => setTab('deposits')}>Deposits</button>
        <button className="d7-btn-outline d7-btn-small" style={tab === 'withdrawals' ? { background: 'rgba(240,165,0,0.1)' } : {}} onClick={() => setTab('withdrawals')}>Withdrawals</button>
      </div>

      {loading && <div className="d7-loading">Loading transactions...</div>}
      {error && <div className="d7-error">{error}</div>}
      {!loading && !error && items.length === 0 && <div className="d7-empty">No {tab} found.</div>}

      {!loading && items.length > 0 && tab === 'deposits' && (
        <table className="d7-table">
          <thead>
            <tr>
              <th>TX Hash</th>
              <th>USDC In</th>
              <th>AGNT Out</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {deposits.map(d => (
              <tr key={d.id}>
                <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.7rem' }}>{d.swap_tx_hash ? `${d.swap_tx_hash.slice(0, 10)}...` : '—'}</td>
                <td>{d.usdc_amount_in || '—'}</td>
                <td style={{ color: 'var(--d7-honey)' }}>{d.agnt_amount_out || '—'}</td>
                <td><Badge type={d.status === 'verified' ? 'available' : 'offline'}>{d.status}</Badge></td>
                <td style={{ fontSize: '0.8rem', color: 'var(--d7-muted)' }}>{new Date(d.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && items.length > 0 && tab === 'withdrawals' && (
        <table className="d7-table">
          <thead>
            <tr>
              <th>Recipient</th>
              <th>AGNT In</th>
              <th>USDC Out</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {withdrawals.map(w => (
              <tr key={w.id}>
                <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.7rem' }}>{w.recipient_address ? `${w.recipient_address.slice(0, 10)}...` : '—'}</td>
                <td>{w.agnt_amount_in || '—'}</td>
                <td style={{ color: 'var(--d7-green)' }}>{w.usdc_amount_out || '—'}</td>
                <td><Badge type={w.status === 'completed' ? 'available' : w.status === 'pending' ? 'busy' : 'offline'}>{w.status}</Badge></td>
                <td style={{ fontSize: '0.8rem', color: 'var(--d7-muted)' }}>{new Date(w.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
