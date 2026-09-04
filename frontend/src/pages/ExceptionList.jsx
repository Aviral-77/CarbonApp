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

const SEVERITY_COLORS = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#dc2626',
}

export default function ExceptionList() {
  const [exceptions, setExceptions] = useState([])
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    const url = filter === 'all' ? '/api/exceptions' : `/api/exceptions?status=${filter}`
    fetch(url).then(r => r.json()).then(setExceptions)
  }, [filter])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>Exceptions</h1>
        <div style={{ display: 'flex', gap: 6 }}>
          {['all', 'open', 'auto_resolved', 'escalated', 'waiting'].map(s => (
            <button key={s} onClick={() => setFilter(s)} style={{
              padding: '6px 14px', borderRadius: 6, border: '1px solid var(--border)',
              background: filter === s ? 'var(--accent)' : 'var(--bg-card)',
              color: filter === s ? '#fff' : 'var(--text-secondary)',
              fontSize: 13, fontWeight: 500, cursor: 'pointer',
              transition: 'all 0.15s',
            }}>
              {s === 'all' ? 'All' : STATUS_LABELS[s] || s}
            </button>
          ))}
        </div>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
        <div style={{
          display: 'grid', gridTemplateColumns: '120px 1fr 180px 120px 100px 80px',
          padding: '10px 20px', borderBottom: '2px solid var(--border)',
          fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5,
        }}>
          <span>ID</span><span>Description</span><span>Supplier</span>
          <span>Type</span><span>Status</span><span>Severity</span>
        </div>

        {exceptions.map(exc => (
          <Link key={exc.id} to={`/exceptions/${exc.id}`} style={{
            display: 'grid', gridTemplateColumns: '120px 1fr 180px 120px 100px 80px',
            padding: '14px 20px', borderBottom: '1px solid var(--border)',
            textDecoration: 'none', color: 'var(--text)', alignItems: 'center',
            fontSize: 14, transition: 'background 0.1s',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: 13 }}>{exc.id}</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', paddingRight: 16 }}>
              {exc.description}
            </span>
            <span style={{ fontSize: 13 }}>{exc.supplier_name}</span>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              {TYPE_LABELS[exc.exception_type]?.split(' ')[0] || exc.exception_type}
            </span>
            <span style={{
              fontSize: 11, fontWeight: 600,
              color: STATUS_COLORS[exc.status],
            }}>
              {STATUS_LABELS[exc.status] || exc.status}
            </span>
            <span style={{
              fontSize: 11, fontWeight: 600,
              color: SEVERITY_COLORS[exc.severity],
            }}>
              {exc.severity}
            </span>
          </Link>
        ))}

        {exceptions.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>
            No exceptions found
          </div>
        )}
      </div>
    </div>
  )
}
