// pages/LoginPage.tsx

import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

export default function LoginPage() {
  const { user, loading, error, loginWithGoogle, loginWithEmail, clearError } = useAuth()
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [mode,     setMode]     = useState<'options' | 'email'>('options')

  if (!loading && user) return <Navigate to="/dashboard" replace />

  return (
    <div className="min-h-screen bg-void flex items-center justify-center relative overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 bg-grid-lines bg-grid opacity-100 pointer-events-none" />

      {/* Ambient glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full opacity-[0.07] pointer-events-none"
        style={{ background: 'radial-gradient(circle, #4af4c8 0%, transparent 65%)' }} />

      {/* Card */}
      <div className="relative w-full max-w-sm mx-4 animate-fade-up">
        <div className="card p-8 space-y-6 border-glow">
          {/* Logo */}
          <div className="text-center space-y-3">
            <div className="inline-flex w-14 h-14 rounded-2xl items-center justify-center"
              style={{ background: 'rgba(74,244,200,0.08)', border: '1px solid rgba(74,244,200,0.2)' }}>
              <span className="text-arc font-display text-2xl font-bold">C</span>
            </div>
            <div>
              <h1 className="font-display text-snow text-2xl font-bold tracking-wide">CAPE</h1>
              <p className="text-ghost text-xs font-mono tracking-widest uppercase mt-0.5">
                Context-Aware Personal Executive
              </p>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-ember/5 border border-ember/25 text-ember text-xs font-body">
              <span className="flex-1">{error}</span>
              <button onClick={clearError} className="opacity-60 hover:opacity-100">✕</button>
            </div>
          )}

          {mode === 'options' ? (
            <div className="space-y-3">
              {/* Google */}
              <button
                onClick={loginWithGoogle}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg border border-border bg-surface hover:bg-white/3 hover:border-muted text-pale text-sm font-body transition-all duration-200"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </button>

              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-border" />
                <span className="text-ghost text-xs font-mono">or</span>
                <div className="flex-1 h-px bg-border" />
              </div>

              <button
                onClick={() => setMode('email')}
                className="btn-arc w-full text-center"
              >
                Sign in with Email
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
                className="input-field"
                autoFocus
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="input-field"
                onKeyDown={(e) => e.key === 'Enter' && loginWithEmail(email, password)}
              />
              <button
                onClick={() => loginWithEmail(email, password)}
                disabled={!email || !password}
                className="btn-arc w-full"
              >
                Sign In
              </button>
              <button onClick={() => setMode('options')} className="btn-ghost w-full text-center text-xs">
                ← Back
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
