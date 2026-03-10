// pages/DashboardPage.tsx — Main AI assistant chat interface

import { useState } from 'react'
import Header from '@/components/layout/Header'
import ChatWindow from '@/components/chat/ChatWindow'
import ChatInput from '@/components/chat/ChatInput'
import { useChat } from '@/hooks/useChat'

export default function DashboardPage() {
  const {
    sessions, activeSessionId, messages, loading, inputError,
    sendMessage, clearChat, setInputError,
    createNewSession, switchSession, deleteSession
  } = useChat()
  const [prefill, setPrefill] = useState<string | undefined>()

  function handleExample(q: string) {
    setPrefill(q)
    // Clear after a tick so re-setting same value re-triggers useEffect
    setTimeout(() => setPrefill(undefined), 100)
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Assistant"
        subtitle={`${messages.length > 0 ? `${messages.length} messages` : 'Ask anything across your knowledge base'}`}
        actions={
          messages.length > 0 ? (
            <button onClick={clearChat} className="btn-ghost text-xs flex items-center gap-1.5">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Clear
            </button>
          ) : undefined
        }
      />

      {/* Main Content Area Split into Left Sidebar (Chats) and Right Chat Area */}
      <div className="flex-1 flex overflow-hidden">

        {/* Chat History Sidebar */}
        <div className="w-64 bg-surface/50 border-r border-border border-t flex flex-col hidden md:flex">
          <div className="p-4 border-b border-border">
            <button
              onClick={() => createNewSession()}
              className="btn-arc w-full flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {sessions.map(session => (
              <div
                key={session.id}
                onClick={() => switchSession(session.id)}
                className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${activeSessionId === session.id ? 'bg-arc/10 text-arc' : 'text-ghost hover:bg-white/5 hover:text-pale'}`}
              >
                <div className="truncate text-xs font-body font-medium flex-1 mr-2" title={session.title}>
                  {session.title || 'New Chat'}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:text-red-400"
                  title="Delete chat"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <div className="text-ghost text-xs text-center mt-6 italic">No recent chats</div>
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatWindow messages={messages} isLoading={loading} onExample={handleExample} />
          <ChatInput
            onSend={sendMessage}
            isLoading={loading}
            error={inputError}
            onClearError={() => setInputError(null)}
            prefill={prefill}
          />
        </div>

      </div>
    </div>
  )
}
