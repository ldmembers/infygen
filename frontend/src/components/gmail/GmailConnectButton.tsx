// components/gmail/GmailConnectButton.tsx
// Clean OAuth redirect flow — no code pasting, no popups.
// Shows Gmail, Drive, and Sheets indexing stats in one unified panel.

import { useEffect, useState } from 'react'
import { startGmailOAuth, syncGmail, getGmailStatus, GmailStatus } from '@/services/gmailService'
import Toast from '@/components/ui/Toast'

interface Props {
  onStatusChange?: (status: GmailStatus) => void
}

export default function GmailConnectButton({ onStatusChange }: Props) {
  const [status, setStatus] = useState<GmailStatus | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' | 'info' } | null>(null)
  const [connecting, setConnecting] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadStatus()

    // Check if we just returned from OAuth
    const params = new URLSearchParams(window.location.search)
    if (params.get('connected') === 'true') {
      setToast({
        msg: '✅ Google account connected! Indexing Gmail, Drive, and Sheets in the background…',
        type: 'success',
      })
      // Clean up URL params without a page reload
      window.history.replaceState({}, '', window.location.pathname)
    } else if (params.get('error')) {
      const errorMsg = decodeURIComponent(params.get('error') || 'Unknown error')
      setToast({ msg: `Connection failed: ${errorMsg}`, type: 'error' })
      window.history.replaceState({}, '', window.location.pathname)
    }

    // Set up polling interval to keep syncing status updated in the background
    const interval = setInterval(() => {
      loadStatus()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  async function loadStatus() {
    setLoadError(null)
    try {
      const s = await getGmailStatus()
      setStatus(s)
      onStatusChange?.(s)
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to load status'
      console.error('Failed to load Gmail status:', msg)
      setLoadError(msg)
    }
  }

  async function handleConnect() {
    setConnecting(true)
    try {
      await startGmailOAuth()
      // Page navigates away after this — setConnecting is just a safety net
    } catch (e) {
      setToast({ msg: e instanceof Error ? e.message : 'Failed to start OAuth', type: 'error' })
      setConnecting(false)
    }
  }

  async function handleSync() {
    setSyncing(true)
    try {
      const data = await syncGmail(50)
      setToast({ msg: data.message, type: 'success' })
      await loadStatus()
    } catch (e) {
      setToast({ msg: e instanceof Error ? e.message : 'Sync failed', type: 'error' })
    } finally {
      setSyncing(false)
    }
  }

  const connected = status?.connected ?? false
  const totalIndexed =
    (status?.emails_indexed ?? 0) +
    (status?.drive_docs_indexed ?? 0) +
    ((status as any)?.sheets_indexed ?? 0)

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} type={toast.type} onDismiss={() => setToast(null)} />}

      {/* Connection status indicator */}
      <div className="flex items-center gap-3 p-4 rounded-lg border border-border bg-surface">
        <div
          className="w-2.5 h-2.5 rounded-full flex-shrink-0 transition-all"
          style={{
            background: connected ? '#4af4c8' : '#8892a4',
            boxShadow: connected ? '0 0 8px rgba(74,244,200,0.5)' : 'none',
          }}
        />
        <div className="flex-1">
          <p className="text-pale text-sm font-body">
            {connected ? 'Google account connected' : 'Google account not connected'}
          </p>
          <p className="text-ghost text-xs font-mono">
            {connected
              ? `Last synced: ${status?.last_synced
                ? new Date(status.last_synced).toLocaleString('en-US', { timeZone: 'Asia/Kolkata', timeStyle: 'medium', dateStyle: 'short' })
                : 'Indexing in progress…'
              }`
              : 'Connect to index Gmail + Drive + Sheets automatically'}
          </p>
        </div>
        {connected && (
          <button
            onClick={loadStatus}
            title="Refresh status"
            className="text-ghost hover:text-arc transition-colors p-1 rounded"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h5M20 20v-5h-5M4 9A9 9 0 0120 15M20 15a9 9 0 01-16 0" />
            </svg>
          </button>
        )}
      </div>

      {/* Error loading status */}
      {loadError && !connected && (
        <div className="px-4 py-3 rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono">
          ⚠ Could not reach backend: {loadError}
        </div>
      )}

      {/* Stats grid (only when connected) */}
      {connected && status && (
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 rounded-lg border border-border bg-surface text-center">
            <p className="text-arc font-mono text-xl font-bold">{status.emails_indexed}</p>
            <p className="text-ghost text-xs font-body mt-1">Emails</p>
          </div>
          <div className="p-3 rounded-lg border border-border bg-surface text-center">
            <p className="text-arc font-mono text-xl font-bold">{status.drive_docs_indexed}</p>
            <p className="text-ghost text-xs font-body mt-1">Drive docs</p>
          </div>
          <div className="p-3 rounded-lg border border-border bg-surface text-center">
            <p className="text-arc font-mono text-xl font-bold">
              {(status as any).sheets_indexed ?? 0}
            </p>
            <p className="text-ghost text-xs font-body mt-1">Sheets</p>
          </div>
        </div>
      )}

      {/* CTA buttons */}
      {!connected ? (
        <button
          onClick={handleConnect}
          disabled={connecting}
          id="gmail-connect-btn"
          className="btn-arc w-full flex items-center justify-center gap-2"
        >
          {connecting ? (
            <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.283 10.356h-8.327v3.451h4.792c-.446 2.193-2.313 3.453-4.792 3.453a5.27 5.27 0 01-5.279-5.28 5.27 5.27 0 015.279-5.279c1.259 0 2.397.447 3.29 1.178l2.6-2.599c-1.584-1.381-3.615-2.233-5.89-2.233a8.908 8.908 0 00-8.934 8.934 8.907 8.907 0 008.934 8.934c4.467 0 8.529-3.249 8.529-8.934 0-.528-.081-1.097-.202-1.625z" />
            </svg>
          )}
          {connecting ? 'Redirecting to Google…' : 'Connect with Google'}
        </button>
      ) : (
        <div className="flex gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            id="gmail-sync-btn"
            className="btn-arc flex-1 flex items-center justify-center gap-2"
          >
            {syncing ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Syncing Gmail…
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h5M20 20v-5h-5M4 9A9 9 0 0120 15M20 15a9 9 0 01-16 0" />
                </svg>
                Re-sync Gmail
              </>
            )}
          </button>
          <button
            onClick={handleConnect}
            disabled={connecting}
            title="Re-connect Google account"
            className="px-3 py-2 rounded-lg border border-border bg-surface text-ghost text-xs font-mono hover:border-arc/30 hover:text-arc transition-all"
          >
            Re-auth
          </button>
        </div>
      )}
    </div>
  )
}
