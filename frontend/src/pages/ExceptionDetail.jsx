import React, { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'

const STATUS_COLORS = {
  open: '#f59e0b', investigating: '#0ea5e9', auto_resolved: '#22c55e',
  escalated: '#ef4444', waiting: '#8b5cf6',
}
const STATUS_LABELS = {
  open: 'Open', investigating: 'Investigating', auto_resolved: 'Auto-Resolved',
  escalated: 'Escalated', waiting: 'Waiting',
}

export default function ExceptionDetail() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [traceEvents, setTraceEvents] = useState([])
  const [investigating, setInvestigating] = useState(false)
  const [complete, setComplete] = useState(false)
  const traceEndRef = useRef(null)

  useEffect(() => {
    fetch(`/api/exceptions/${id}`).then(r => r.json()).then(setData)
  }, [id])

  useEffect(() => {
    if (traceEndRef.current) {
      traceEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [traceEvents])

  const startInvestigation = () => {
    setInvestigating(true)
    setComplete(false)
    setTraceEvents([])

    const es = new EventSource(`/api/exceptions/${id}/investigate`)
    es.onmessage = (event) => {
      const parsed = JSON.parse(event.data)
      setTraceEvents(prev => [...prev, parsed])
      if (parsed.type === 'complete' || parsed.type === 'error') {
        setInvestigating(false)
        setComplete(true)
        es.close()
        fetch(`/api/exceptions/${id}`).then(r => r.json()).then(setData)
      }
    }
    es.onerror = () => {
      setInvestigating(false)
      es.close()
    }
  }

  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>Loading...</div>

  const { exception: exc, records, audit_trail } = data

  return (
    <div>
      <Link to="/exceptions" style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'inline-block', marginBottom: 16 }}>
        &larr; Back to Exceptions
      </Link>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>{exc.id}</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 600 }}>{exc.description}</p>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600,
            color: STATUS_COLORS[exc.status], background: `${STATUS_COLORS[exc.status]}18`,
          }}>
            {STATUS_LABELS[exc.status] || exc.status}
          </span>
          {exc.status === 'open' && (
            <button onClick={startInvestigation} disabled={investigating} style={{
              padding: '8px 20px', borderRadius: 8, border: 'none',
              background: investigating ? 'var(--bg-hover)' : 'var(--accent)',
              color: investigating ? 'var(--text-secondary)' : '#fff',
              fontSize: 14, fontWeight: 600, cursor: investigating ? 'default' : 'pointer',
            }}>
              {investigating ? 'Investigating...' : 'Investigate'}
            </button>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        <Section title="Exception Details">
          <InfoRow label="Supplier" value={exc.supplier_name} />
          <InfoRow label="Type" value={exc.exception_type} />
          <InfoRow label="Severity" value={exc.severity} />
          <InfoRow label="Created" value={new Date(exc.created_at).toLocaleString()} />
          {exc.resolved_at && <InfoRow label="Resolved" value={new Date(exc.resolved_at).toLocaleString()} />}
          {exc.resolved_by && <InfoRow label="Resolved By" value={exc.resolved_by} />}
        </Section>

        <Section title="Source Records">
          {records.filter(r => r.reporting_period === records[0]?.reporting_period).map(r => (
            <div key={r.id} style={{
              display: 'flex', justifyContent: 'space-between', padding: '8px 0',
              borderBottom: '1px solid var(--border)', fontSize: 14,
            }}>
              <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                {r.source.replace('_', ' ')}
              </span>
              <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                {Number(r.quantity).toLocaleString()} {r.unit}
              </span>
            </div>
          ))}
        </Section>
      </div>

      {(traceEvents.length > 0 || investigating) && (
        <Section title="Investigation Trace" style={{ marginBottom: 24 }}>
          <div style={{
            background: '#0f172a', borderRadius: 8, padding: 16,
            maxHeight: 500, overflowY: 'auto', fontFamily: 'monospace', fontSize: 13,
          }}>
            {traceEvents.map((evt, i) => (
              <TraceEvent key={i} event={evt} />
            ))}
            {investigating && (
              <div style={{ color: '#94a3b8', padding: '4px 0' }}>
                <span style={{ animation: 'pulse 1.5s infinite' }}>Processing...</span>
              </div>
            )}
            <div ref={traceEndRef} />
          </div>
        </Section>
      )}

      {audit_trail.length > 0 && (
        <Section title="Audit Trail">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {audit_trail.map((evt, i) => (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '180px 140px 140px 1fr',
                padding: '10px 0', borderBottom: '1px solid var(--border)',
                fontSize: 13, alignItems: 'start',
              }}>
                <span style={{ color: 'var(--text-secondary)' }}>
                  {new Date(evt.timestamp).toLocaleString()}
                </span>
                <span style={{ fontWeight: 600 }}>{evt.action}</span>
                <span style={{ color: 'var(--text-secondary)' }}>{evt.agent || '-'}</span>
                <span style={{ color: 'var(--text-secondary)' }}>
                  {evt.reasoning || evt.policy_applied || ''}
                  {evt.confidence != null && ` (confidence: ${evt.confidence})`}
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

function Section({ title, children, style }) {
  return (
    <div style={{
      background: 'var(--bg-card)', borderRadius: 12,
      border: '1px solid var(--border)', padding: 20, ...style,
    }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 14 }}>
      <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{ fontWeight: 500 }}>{value}</span>
    </div>
  )
}

function TraceEvent({ event }) {
  const colors = {
    tool_call: '#0ea5e9',
    tool_result: '#22c55e',
    text: '#e2e8f0',
    complete: '#22c55e',
    error: '#ef4444',
    heartbeat: '#334155',
  }
  const icons = {
    tool_call: '→',
    tool_result: '←',
    text: '·',
    complete: '✓',
    error: '✗',
  }

  if (event.type === 'heartbeat') return null

  return (
    <div style={{ padding: '4px 0', color: colors[event.type] || '#e2e8f0' }}>
      <span style={{ marginRight: 8 }}>{icons[event.type] || '·'}</span>
      {event.type === 'tool_call' && (
        <span>
          <span style={{ fontWeight: 600 }}>{event.tool}</span>
          <span style={{ color: '#64748b', marginLeft: 8 }}>
            {JSON.stringify(event.input).substring(0, 120)}
          </span>
        </span>
      )}
      {event.type === 'tool_result' && (
        <span>
          <span style={{ fontWeight: 600 }}>{event.tool}</span>
          <span style={{ color: '#64748b', marginLeft: 8 }}>
            {event.output?.substring(0, 200)}
          </span>
        </span>
      )}
      {event.type === 'text' && <span>{event.text}</span>}
      {event.type === 'complete' && <span style={{ fontWeight: 600 }}>Investigation complete</span>}
      {event.type === 'error' && <span style={{ fontWeight: 600 }}>Error: {event.message}</span>}
    </div>
  )
}
