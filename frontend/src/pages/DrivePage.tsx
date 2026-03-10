// pages/DrivePage.tsx
// Read-only view of indexed Drive files.
// Authentication is handled via Gmail OAuth (same Google token).

import { useEffect, useState } from 'react'
import Header from '@/components/layout/Header'
import driveService, { IndexedFile } from '@/services/driveService'
import { getGmailStatus } from '@/services/gmailService'
import { useNavigate } from 'react-router-dom'

export default function DrivePage() {
    const [files, setFiles] = useState<IndexedFile[]>([])
    const [loading, setLoading] = useState(true)
    const [syncing, setSyncing] = useState(false)
    const [connected, setConnected] = useState(false)
    const navigate = useNavigate()

    useEffect(() => {
        loadData()
    }, [])

    async function loadData() {
        setLoading(true)
        try {
            const [gmailStatus, fileList] = await Promise.all([
                getGmailStatus(),
                driveService.listFiles(),
            ])
            setConnected(gmailStatus.connected)
            setFiles(fileList)
        } catch (err) {
            console.error('Failed to load Drive data', err)
        } finally {
            setLoading(false)
        }
    }

    async function handleSync() {
        setSyncing(true)
        try {
            await driveService.sync()
            await loadData()
        } catch {
            console.error('Drive sync failed')
        } finally {
            setSyncing(false)
        }
    }

    return (
        <div className="flex flex-col h-screen overflow-hidden">
            <Header
                title="Google Drive"
                subtitle="Documents indexed from your Drive via the Gmail connection"
            />
            <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="max-w-4xl mx-auto space-y-6">

                    {/* Status bar */}
                    <div className="card p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div
                                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                                style={{
                                    background: connected ? '#4af4c8' : '#8892a4',
                                    boxShadow: connected ? '0 0 8px rgba(74,244,200,0.5)' : 'none',
                                }}
                            />
                            <div>
                                <p className="text-pale text-sm font-body">
                                    {connected ? 'Google account connected' : 'Google account not connected'}
                                </p>
                                <p className="text-ghost text-xs font-mono">
                                    {connected
                                        ? `${files.length} file${files.length !== 1 ? 's' : ''} indexed`
                                        : 'Connect via the Gmail page to index Drive files'}
                                </p>
                            </div>
                        </div>

                        {connected ? (
                            <button
                                onClick={handleSync}
                                disabled={syncing}
                                id="drive-sync-btn"
                                className="px-4 py-2 bg-white/5 text-pale border border-border rounded-lg font-mono text-sm hover:bg-white/10 disabled:opacity-50 transition-all"
                            >
                                {syncing ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                        </svg>
                                        Syncing…
                                    </span>
                                ) : 'Re-sync Drive'}
                            </button>
                        ) : (
                            <button
                                onClick={() => navigate('/gmail')}
                                className="px-4 py-2 bg-arc/10 text-arc border border-arc/20 rounded-lg font-mono text-sm hover:bg-arc/20 transition-all"
                            >
                                Connect Google →
                            </button>
                        )}
                    </div>

                    {/* Files table */}
                    <div className="card overflow-hidden">
                        <div className="px-5 py-4 border-b border-border">
                            <h2 className="font-display text-snow text-sm font-semibold">Indexed Files</h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left font-body text-sm">
                                <thead>
                                    <tr className="bg-white/3 border-b border-border">
                                        <th className="px-6 py-3 text-ghost font-mono text-xs uppercase tracking-wider">Name</th>
                                        <th className="px-6 py-3 text-ghost font-mono text-xs uppercase tracking-wider hidden md:table-cell">Drive ID</th>
                                        <th className="px-6 py-3 text-ghost font-mono text-xs uppercase tracking-wider">Indexed At</th>
                                        <th className="px-6 py-3 text-ghost font-mono text-xs uppercase tracking-wider">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {loading ? (
                                        <tr>
                                            <td colSpan={4} className="px-6 py-10 text-center text-ghost font-mono text-sm">
                                                <span className="flex items-center justify-center gap-2">
                                                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                                                    </svg>
                                                    Loading…
                                                </span>
                                            </td>
                                        </tr>
                                    ) : files.length > 0 ? (
                                        files.map((file) => (
                                            <tr key={file.id} className="hover:bg-white/2 transition-colors">
                                                <td className="px-6 py-4 text-snow">{file.name}</td>
                                                <td className="px-6 py-4 text-ghost font-mono text-xs truncate max-w-[150px] hidden md:table-cell">
                                                    {file.document_id}
                                                </td>
                                                <td className="px-6 py-4 text-ghost">
                                                    {file.indexed_at ? new Date(file.indexed_at).toLocaleDateString() : '—'}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="px-2 py-1 rounded bg-arc/10 text-arc text-[10px] font-mono border border-arc/20 uppercase">
                                                        {file.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={4} className="px-6 py-10 text-center text-ghost font-mono text-sm">
                                                {connected
                                                    ? 'No Drive files indexed yet. Click Re-sync Drive above.'
                                                    : 'Connect Google on the Gmail page to start indexing Drive files.'}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    )
}
