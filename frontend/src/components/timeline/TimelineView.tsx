// components/timeline/TimelineView.tsx

import Badge from '@/components/ui/Badge'

export interface TimelineEvent {
  date:   string
  text:   string
  source: string
  file:   string
}

interface Props {
  events:     TimelineEvent[]
  summary?:   string
  confidence?: string
}

export default function TimelineView({ events, summary, confidence }: Props) {
  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-ghost text-sm font-mono opacity-50">
        No dated events found. Try a query with a specific topic.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      {summary && (
        <div className="p-4 rounded-xl border border-pulse/20 bg-pulse/5 text-pale text-sm font-body leading-relaxed">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-pulse font-mono text-xs">AI SUMMARY</span>
            {confidence && <span className="text-ghost font-mono text-[10px]">· {confidence} confidence</span>}
          </div>
          {summary}
        </div>
      )}

      {/* Timeline */}
      <div className="relative pl-6">
        {/* Vertical line */}
        <div className="absolute left-2 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-5">
          {events.map((event, i) => (
            <div key={i} className="relative animate-fade-up" style={{ animationDelay: `${i * 60}ms` }}>
              {/* Dot */}
              <div
                className="absolute -left-4 top-1.5 w-2 h-2 rounded-full"
                style={{ background: '#4af4c8', boxShadow: '0 0 6px rgba(74,244,200,0.5)' }}
              />

              <div className="pl-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-arc font-mono text-xs font-semibold">{event.date}</span>
                  <Badge label={event.source} />
                  {event.file && (
                    <span className="text-ghost font-mono text-[10px] truncate max-w-[160px]">{event.file}</span>
                  )}
                </div>
                <p className="text-pale text-sm font-body leading-relaxed">{event.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
