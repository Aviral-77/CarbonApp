import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const STATUS_COLORS = {
  open: '#f59e0b',
  investigating: '#0ea5e9',
  auto_resolved: '#22c55e',
  escalated: '#ef4444',
  waiting: '#8b5cf6',
}

const STATUS_LABELS = {
  open: 'Open',
  investigating: 'Investigating',
  auto_resolved: 'Auto-Resolved',
  escalated: 'Escalated',
  waiting: 'Waiting',
}

const TYPE_LABELS = {
  transcription_error: 'Transcription Error',
  missing_data: 'Missing Data',
  cross_source_mismatch: 'Cross-Source Mismatch',
  historical_deviation: 'Historical Deviation',
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [exceptions, setExceptions] = useState([])

  useEffect(() => {
    fetch('/api/dashboard').then(r => r.json()).then(setData)
    fetch('/api/exceptions').then(r => r.json()).then(setExceptions)
  }, [])

  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>Loading...</div>

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Dashboard</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard label="Total Exceptions" value={data.total_exceptions} color="var(--accent)" />
        {Object.entries(data.by_status).map(([status, count]) => (
          <StatCard key={status} label={STATUS_LABELS[status] || status} value={count} color={STATUS_COLORS[status] || '#64748b'} />
        ))}
      </div>

      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>By Type</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 32 }}>
        {Object.entries(data.by_type).map(([type, count]) => (
          <StatCard key={type} label={TYPE_LABELS[type] || type} value={count} color="var(--text-secondary)" />
        ))}
      </div>

      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Recent Exceptions</h2>
      <div style={{ background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
        {exceptions.slice(0, 5).map(exc => (
          <Link key={exc.id} to={`/exceptions/${exc.id}`} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '14px 20px', borderBottom: '1px solid var(--border)',
            textDecoration: 'none', color: 'var(--text)',
            transition: 'background 0.1s',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{exc.id}</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
                {exc.supplier_name} — {TYPE_LABELS[exc.exception_type] || exc.exception_type}
              </div>
            </div>
            <StatusBadge status={exc.status} />
          </Link>
        ))}
      </div>
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: 12,
      border: '1px solid var(--border)',
      padding: '20px',
    }}>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 700, color }}>{value}</div>
    </div>
  )
}

function StatusBadge({ status }) {
  return (
    <span style={{
      padding: '4px 10px',
      borderRadius: 20,
      fontSize: 12,
      fontWeight: 600,
      color: STATUS_COLORS[status] || '#64748b',
      background: `${STATUS_COLORS[status] || '#64748b'}18`,
    }}>
      {STATUS_LABELS[status] || status}
    </span>
  )
}
