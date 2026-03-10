// pages/TimelinePage.tsx

import { useState } from 'react'
import Header from '@/components/layout/Header'
import TimelineView, { type TimelineEvent } from '@/components/timeline/TimelineView'
import apiClient from '@/services/apiClient'
import { ENDPOINTS } from '@/config/api'
import Toast from '@/components/ui/Toast'

interface TimelineResponse {
  query:      string
  events:     TimelineEvent[]
  summary:    string
  confidence: string
}

export default function TimelinePage() {
  const [query,    setQuery]    = useState('')
  const [result,   setResult]   = useState<TimelineResponse | null>(null)
  const [loading,  setLoading]  = useState(false)
  const [toast,    setToast]    = useState<{ msg: string; type: 'error' | 'info' } | null>(null)

  async function handleSearch() {
    const q = query.trim()
    if (!q) { setToast({ msg: 'Enter a topic to build a timeline.', type: 'info' }); return }
    setLoading(true); setResult(null); setToast(null)
    try {
      const { data } = await apiClient.get<TimelineResponse>(ENDPOINTS.timeline, { params: { query: q } })
      setResult(data)
      if (data.events.length === 0) {
        setToast({ msg: 'No dated events found for this query. Try a different topic.', type: 'info' })
      }
    } catch (e) {
      setToast({ msg: e instanceof Error ? e.message : 'Timeline request failed', type: 'error' })
    } finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Timeline"
        subtitle="Reconstruct a chronological view of any topic across your sources"
      />
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto space-y-5">
          {toast && <Toast message={toast.msg} type={toast.type} onDismiss={() => setToast(null)} />}

          {/* Search */}
          <div className="flex gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. event planning, project decisions, budget discussions"
              className="input-field flex-1"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="btn-arc flex items-center gap-2 flex-shrink-0"
            >
              {loading ? (
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
              ) : (
                <span className="font-mono">⟳</span>
              )}
              {loading ? 'Building…' : 'Build Timeline'}
            </button>
          </div>

          {/* Example queries */}
          {!result && !loading && (
            <div className="flex flex-wrap gap-2">
              {['event logistics', 'project milestones', 'budget decisions', 'catering vendor'].map((ex) => (
                <button
                  key={ex}
                  onClick={() => setQuery(ex)}
                  className="text-xs font-mono px-3 py-1.5 rounded-full border border-border text-ghost hover:border-arc/30 hover:text-arc/80 transition-all duration-200"
                >
                  {ex}
                </button>
              ))}
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-ghost text-xs font-mono">
                  {result.events.length} event(s) found for "{result.query}"
                </span>
              </div>
              <TimelineView
                events={result.events}
                summary={result.summary}
                confidence={result.confidence}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
