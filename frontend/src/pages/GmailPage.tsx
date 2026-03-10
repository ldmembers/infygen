// pages/GmailPage.tsx
// Connection hub for Gmail + Drive + Sheets (single OAuth connection).

import { useState, useEffect } from 'react'
import Header from '@/components/layout/Header'
import GmailConnectButton from '@/components/gmail/GmailConnectButton'
import { GmailStatus, getGmailFiles, getDriveFiles, IndexedFile } from '@/services/gmailService'

export default function GmailPage() {
  const [status, setStatus] = useState<GmailStatus | null>(null)
  const [gmailFiles, setGmailFiles] = useState<IndexedFile[]>([])
  const [driveFiles, setDriveFiles] = useState<IndexedFile[]>([])

  // Poll for files as well when connected
  useEffect(() => {
    if (!status?.connected) return
    const fetchFiles = async () => {
      try {
        const [gFiles, dFiles] = await Promise.all([getGmailFiles(), getDriveFiles()])
        setGmailFiles(gFiles)
        setDriveFiles(dFiles)
      } catch (e) {
        console.error("Failed to load synced files", e)
      }
    }
    fetchFiles() // Initial load
    const int = setInterval(fetchFiles, 7000)
    return () => clearInterval(int)
  }, [status?.connected, status?.last_synced])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Gmail"
        subtitle="Connect Google to index Gmail, Drive, and Sheets automatically"
      />
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-xl mx-auto space-y-6">

          {/* Connection widget */}
          <div className="card p-5">
            <h3 className="font-display text-snow text-sm font-semibold mb-4">
              Google Account
            </h3>
            <GmailConnectButton onStatusChange={setStatus} />
          </div>

          {/* What gets indexed */}
          <div className="card p-5 space-y-3">
            <h3 className="font-display text-snow text-sm font-semibold">
              What gets indexed
            </h3>
            <ul className="space-y-2 text-ghost text-sm font-body">
              {[
                {
                  icon: '✉',
                  label: 'Gmail — recent 50 messages + attachments (PDF, CSV, TXT)',
                  indexed: status?.emails_indexed,
                },
                {
                  icon: '⊞',
                  label: 'Google Drive — PDFs, Docs, CSVs, text files',
                  indexed: status?.drive_docs_indexed,
                },
                {
                  icon: '⊟',
                  label: 'Google Sheets — rows converted to natural language',
                  indexed: status?.sheets_indexed,
                },
              ].map((item) => (
                <li key={item.icon} className="flex items-center gap-3">
                  <span className="text-arc font-mono text-sm w-4">{item.icon}</span>
                  <span className="flex-1">{item.label}</span>
                  {item.indexed !== undefined && item.indexed > 0 && (
                    <span className="px-2 py-0.5 rounded bg-arc/10 text-arc text-[10px] font-mono border border-arc/20">
                      {item.indexed} indexed
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* How it works */}
          <div className="card p-5">
            <h3 className="font-display text-snow text-sm font-semibold mb-3">How it works</h3>
            <ol className="space-y-2 text-ghost text-sm font-body">
              {[
                'Click "Connect with Google" — you\'ll be redirected to Google\'s login page',
                'Grant read-only access to Gmail, Drive, and Sheets',
                'You\'re redirected back here; indexing starts automatically in the background',
                'Ask questions about your emails and documents in the Assistant',
              ].map((step, i) => (
                <li key={i} className="flex gap-3">
                  <span className="text-arc font-mono text-xs mt-0.5 flex-shrink-0 w-5">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Permissions note */}
          <div className="px-4 py-3 rounded-lg border border-border text-ghost text-xs font-mono leading-relaxed">
            ⚠ Requests <span className="text-pale">read-only</span> access.
            Embeddings are computed locally — your data stays on your machine.
          </div>

          {/* Sync History Table (Displays isolated lists to the user) */}
          {status?.connected && (gmailFiles.length > 0 || driveFiles.length > 0) && (
            <div className="card p-5 space-y-4">
              <h3 className="font-display text-snow text-sm font-semibold mb-3">Recently Synced Documents & Emails</h3>

              {gmailFiles.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-arc text-xs font-mono mb-2">📥 Indexed Gmail Items</h4>
                  <div className="max-h-48 overflow-y-auto space-y-1.5 pr-2">
                    {gmailFiles.slice(0, 30).map(f => (
                      <div key={f.id} className="text-xs font-body text-ghost flex justify-between bg-surface/50 p-2 rounded border border-white/5">
                        <span className="truncate flex-1 mr-4">{f.name}</span>
                        <span className="font-mono text-[10px] opacity-60">
                          {f.indexed_at ? new Date(f.indexed_at).toLocaleDateString() : 'Syncing'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {driveFiles.length > 0 && (
                <div className="space-y-2 mt-4">
                  <h4 className="text-arc text-xs font-mono mb-2">☁ Indexed Drive Documents</h4>
                  <div className="max-h-48 overflow-y-auto space-y-1.5 pr-2">
                    {driveFiles.slice(0, 30).map(f => (
                      <div key={f.id} className="text-xs font-body text-ghost flex justify-between bg-surface/50 p-2 rounded border border-white/5">
                        <span className="truncate flex-1 mr-4">{f.name}</span>
                        <span className="font-mono text-[10px] opacity-60">
                          {f.indexed_at ? new Date(f.indexed_at).toLocaleDateString() : 'Syncing'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
