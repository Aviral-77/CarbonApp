import React from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ExceptionList from './pages/ExceptionList'
import ExceptionDetail from './pages/ExceptionDetail'

export default function App() {
  const location = useLocation()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        background: 'var(--bg-card)',
        borderBottom: '1px solid var(--border)',
        padding: '0 24px',
        height: 56,
        display: 'flex',
        alignItems: 'center',
        gap: 32,
      }}>
        <Link to="/" style={{
          fontWeight: 700,
          fontSize: 18,
          color: 'var(--text)',
          textDecoration: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{
            background: 'linear-gradient(135deg, #0ea5e9, #22c55e)',
            borderRadius: 6,
            width: 28,
            height: 28,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 14,
            fontWeight: 700,
          }}>C</span>
          CarbonOps
        </Link>
        <nav style={{ display: 'flex', gap: 4 }}>
          {[
            { to: '/', label: 'Dashboard' },
            { to: '/exceptions', label: 'Exceptions' },
          ].map(({ to, label }) => (
            <Link key={to} to={to} style={{
              padding: '6px 14px',
              borderRadius: 6,
              fontSize: 14,
              fontWeight: 500,
              color: location.pathname === to ? 'var(--accent)' : 'var(--text-secondary)',
              background: location.pathname === to ? 'var(--bg-hover)' : 'transparent',
              textDecoration: 'none',
              transition: 'all 0.15s',
            }}>
              {label}
            </Link>
          ))}
        </nav>
      </header>

      <main style={{ flex: 1, padding: 24, maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/exceptions" element={<ExceptionList />} />
          <Route path="/exceptions/:id" element={<ExceptionDetail />} />
        </Routes>
      </main>
    </div>
  )
}
