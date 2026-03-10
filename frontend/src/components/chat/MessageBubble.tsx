// components/chat/MessageBubble.tsx

import type { ChatMessage } from '@/hooks/useChat'
import Badge from '@/components/ui/Badge'

interface Props { message: ChatMessage }

function ConfidenceBar({ confidence }: { confidence: string }) {
  const pct = parseInt(confidence, 10) || 0
  const color = pct >= 75 ? '#4af4c8' : pct >= 50 ? '#f4804a' : '#ff5f5f'
  return (
    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
      <span className="text-ghost text-[10px] font-mono whitespace-nowrap">confidence</span>
      <div className="flex-1 h-0.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full conf-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-[10px] font-mono font-semibold" style={{ color }}>{confidence}</span>
    </div>
  )
}

/** Render a single line of text with inline markdown: **bold**, *italic*, `code` */
function renderLine(line: string, index: number) {
  const html = line
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(
      /`(.*?)`/g,
      '<code style="background:rgba(74,244,200,0.08);padding:1px 4px;border-radius:3px;font-family:monospace;font-size:0.85em;">$1</code>'
    )

  if (!html.trim()) return <br key={index} />
  return (
    <p
      key={index}
      className="leading-relaxed"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const isError = message.role === 'error'
  const isAssistant = message.role === 'assistant'

  return (
    <div className={`flex gap-3 animate-fade-up ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-mono mt-0.5"
        style={
          isUser
            ? { background: 'rgba(107,140,255,0.15)', border: '1px solid rgba(107,140,255,0.3)', color: '#6b8cff' }
            : isError
              ? { background: 'rgba(255,95,95,0.1)', border: '1px solid rgba(255,95,95,0.3)', color: '#ff5f5f' }
              : { background: 'rgba(74,244,200,0.1)', border: '1px solid rgba(74,244,200,0.25)', color: '#4af4c8' }
        }
      >
        {isUser ? 'U' : isError ? '!' : 'AI'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div
          className="rounded-xl px-4 py-3 text-sm font-body leading-relaxed"
          style={
            isUser
              ? { background: 'rgba(107,140,255,0.08)', border: '1px solid rgba(107,140,255,0.2)', color: '#c5ccd8' }
              : isError
                ? { background: 'rgba(255,95,95,0.05)', border: '1px solid rgba(255,95,95,0.2)', color: '#ff8080' }
                : { background: '#12151a', border: '1px solid #1e2229', color: '#c5ccd8' }
          }
        >
          {/* Render message with simple inline markdown */}
          <div className="space-y-1.5">
            {message.content.split('\n').map((line, i) => renderLine(line, i))}
          </div>

          {/* AI metadata: sources + confidence */}
          {isAssistant && (message.sources?.length || message.confidence) && (
            <div className="mt-3">
              {message.sources && message.sources.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-1">
                  {message.sources.map((s) => <Badge key={s} label={s} />)}
                </div>
              )}
              {message.confidence && <ConfidenceBar confidence={message.confidence} />}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-[10px] font-mono text-ghost opacity-60 px-1">{message.timestamp}</span>
      </div>
    </div>
  )
}
