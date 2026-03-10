// components/layout/Sidebar.tsx

import { NavLink } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

interface NavItem {
  to: string
  label: string
  icon: string
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Assistant', icon: '◈' },
  { to: '/gmail', label: 'Gmail', icon: '✉' },
  { to: '/memory', label: 'Memory', icon: '◎' },
  { to: '/timeline', label: 'Timeline', icon: '⟳' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="w-56 flex-shrink-0 flex flex-col h-screen bg-surface border-r border-border relative z-10">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: 'rgba(74,244,200,0.1)', border: '1px solid rgba(74,244,200,0.25)' }}>
            <span className="text-arc text-xs font-mono font-bold">C</span>
          </div>
          <div>
            <div className="font-display text-snow text-sm font-semibold tracking-wide">CAPE</div>
            <div className="text-ghost font-mono text-[9px] tracking-widest uppercase">Executive AI</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-body transition-all duration-150 group ${isActive
                ? 'text-arc bg-arc/8 border border-arc/20'
                : 'text-ghost hover:text-pale hover:bg-white/3 border border-transparent'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span className={`font-mono text-base ${isActive ? 'text-arc' : 'text-ghost group-hover:text-pale'}`}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-arc" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User section */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg">
          <div className="w-7 h-7 rounded-full flex items-center justify-center bg-muted text-ghost text-xs font-mono flex-shrink-0">
            {user?.email?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-pale text-xs font-body truncate">
              {user?.displayName ?? user?.email ?? 'User'}
            </div>
            <div className="text-ghost text-[10px] font-mono">authenticated</div>
          </div>
          <button
            onClick={logout}
            className="text-ghost hover:text-ember transition-colors p-1 rounded"
            title="Sign out"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  )
}
