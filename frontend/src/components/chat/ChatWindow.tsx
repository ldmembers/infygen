// components/chat/ChatWindow.tsx

import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import type { ChatMessage } from '@/hooks/useChat'

const EXAMPLE_QUERIES = [
  'What did we decide about event logistics?',
  'Summarise the Q4 budget from the emails',
  'Which tasks are high priority and incomplete?',
  'Give me a timeline of the project decisions',
]

interface Props {
  messages:   ChatMessage[]
  isLoading:  boolean
  onExample?: (q: string) => void
}

function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-mono"
        style={{ background: 'rgba(74,244,200,0.1)', border: '1px solid rgba(74,244,200,0.25)', color: '#4af4c8' }}>
        AI
      </div>
      <div className="rounded-xl px-4 py-3" style={{ background: '#12151a', border: '1px solid #1e2229' }}>
        <div className="flex items-center gap-1.5 h-5">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  )
}

export default function ChatWindow({ messages, isLoading, onExample }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-8 py-12">
        {/* Ambient glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full opacity-5 pointer-events-none"
          style={{ background: 'radial-gradient(circle, #4af4c8 0%, transparent 70%)' }} />

        <div className="relative text-center max-w-md">
          <div className="inline-flex w-14 h-14 rounded-2xl items-center justify-center mb-4"
            style={{ background: 'rgba(74,244,200,0.06)', border: '1px solid rgba(74,244,200,0.2)' }}>
            <span className="text-arc font-mono text-2xl">◈</span>
          </div>
          <h2 className="font-display text-snow text-xl font-semibold mb-2">Ask your executive assistant</h2>
          <p className="text-ghost text-sm font-body leading-relaxed mb-8">
            I search across your emails, documents, tasks, and memories to give you one clear answer.
          </p>
          <div className="grid grid-cols-1 gap-2">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => onExample?.(q)}
                className="text-left px-4 py-2.5 rounded-lg text-xs font-mono text-ghost border border-border hover:border-arc/30 hover:text-arc/80 hover:bg-arc/3 transition-all duration-200"
              >
                "{q}"
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isLoading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  )
}
