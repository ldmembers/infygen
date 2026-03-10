// components/chat/ChatInput.tsx

import { useState, useRef, useEffect, type KeyboardEvent } from 'react'

interface Props {
  onSend:      (query: string) => void
  isLoading:   boolean
  error?:      string | null
  onClearError?: () => void
  prefill?:    string
}

export default function ChatInput({ onSend, isLoading, error, onClearError, prefill }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Accept prefill from parent (example queries)
  useEffect(() => {
    if (prefill) {
      setValue(prefill)
      textareaRef.current?.focus()
    }
  }, [prefill])

  // Auto-resize
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }, [value])

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleSend() {
    if (!value.trim() || isLoading) return
    onSend(value.trim())
    setValue('')
  }

  return (
    <div className="px-6 pb-5 pt-2">
      {error && (
        <div className="mb-2 flex items-center gap-2 px-3 py-2 rounded-lg bg-ember/5 border border-ember/25 text-ember text-xs font-mono">
          <span className="flex-1">{error}</span>
          <button onClick={onClearError} className="opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      <div
        className="flex items-end gap-3 rounded-xl px-4 py-3 transition-all duration-200"
        style={{
          background: '#12151a',
          border: '1px solid #1e2229',
          boxShadow: value ? '0 0 0 1px rgba(74,244,200,0.15), 0 0 20px rgba(74,244,200,0.04)' : 'none',
        }}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask across your emails, documents, tasks and memories…"
          rows={1}
          disabled={isLoading}
          className="flex-1 resize-none bg-transparent text-sm font-body text-pale placeholder-ghost outline-none leading-relaxed min-h-[22px] disabled:opacity-50"
          style={{ maxHeight: 140 }}
        />

        <button
          onClick={handleSend}
          disabled={!value.trim() || isLoading}
          className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 disabled:opacity-25 disabled:cursor-not-allowed"
          style={{
            background: value.trim() && !isLoading ? 'rgba(74,244,200,0.15)' : 'rgba(74,244,200,0.04)',
            border: `1px solid ${value.trim() && !isLoading ? 'rgba(74,244,200,0.4)' : 'rgba(74,244,200,0.1)'}`,
          }}
        >
          {isLoading ? (
            <svg className="animate-spin w-3.5 h-3.5 text-arc" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
          ) : (
            <svg className="w-3.5 h-3.5 text-arc" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          )}
        </button>
      </div>

      <p className="text-center text-[10px] font-mono text-ghost opacity-40 mt-2">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
