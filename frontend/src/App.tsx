// App.tsx — Routing, auth guard, and layout wrapper

import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import Sidebar from '@/components/layout/Sidebar'

import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import DrivePage from '@/pages/DrivePage'
import GmailPage from '@/pages/GmailPage'
import MemoryPage from '@/pages/MemoryPage'
import TimelinePage from '@/pages/TimelinePage'

// ── Auth guard ────────────────────────────────────────────────────────────────
function RequireAuth() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 rounded-full border-2 border-arc border-t-transparent animate-spin" />
          <span className="text-ghost font-mono text-sm">Authenticating…</span>
        </div>
      </div>
    )
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />
}

// ── Authenticated shell with sidebar ─────────────────────────────────────────
function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-void relative z-10">
      <Sidebar />
      <main className="flex-1 overflow-hidden bg-surface relative">
        {/* Subtle grid */}
        <div className="absolute inset-0 bg-grid-lines bg-grid opacity-30 pointer-events-none" />
        <div className="relative z-10 h-full">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/drive" element={<DrivePage />} />
            <Route path="/gmail" element={<GmailPage />} />
            <Route path="/memory" element={<MemoryPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
          </Route>
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
