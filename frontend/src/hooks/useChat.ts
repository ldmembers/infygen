// hooks/useChat.ts
// Manages chat conversation state and API calls.

import { useState, useCallback, useEffect } from 'react'
import { askQuestion, type AskResponse } from '@/services/assistantService'
import { validateQuery } from '@/utils/validators'
import { useAuth } from '@/hooks/useAuth'

export type MessageRole = 'user' | 'assistant' | 'error'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: string
  confidence?: string
  sources?: string[]
}

export interface ChatSession {
  id: string
  title: string
  updatedAt: number
  messages: ChatMessage[]
}

let _id = 0
function nextId() { return `msg-${Date.now()}-${++_id}` }
function now() { return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }

export function useChat() {
  const { user } = useAuth()

  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)

  const [loading, setLoading] = useState(false)
  const [inputError, setInputError] = useState<string | null>(null)

  // Load from localStorage on mount or user change
  useEffect(() => {
    if (!user) {
      setSessions([])
      setActiveSessionId(null)
      return
    }
    const key = `cape_chats_${user.uid}`
    const stored = localStorage.getItem(key)
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as ChatSession[]
        setSessions(parsed)
        if (parsed.length > 0) setActiveSessionId(parsed[0].id)
      } catch (e) {
        setSessions([])
      }
    } else {
      setSessions([])
      setActiveSessionId(null)
    }
  }, [user])

  // Save to localStorage whenever sessions change
  useEffect(() => {
    if (!user) return
    const key = `cape_chats_${user.uid}`
    localStorage.setItem(key, JSON.stringify(sessions))
  }, [sessions, user])

  const activeSession = sessions.find(s => s.id === activeSessionId)
  const messages = activeSession?.messages || []

  const createNewSession = useCallback((title: string = 'New Chat') => {
    const newSession: ChatSession = { id: `chat-${Date.now()}`, title, updatedAt: Date.now(), messages: [] }
    setSessions(prev => [newSession, ...prev])
    setActiveSessionId(newSession.id)
  }, [])

  const switchSession = useCallback((id: string) => {
    setActiveSessionId(id)
  }, [])

  const deleteSession = useCallback((id: string) => {
    setSessions(prev => {
      const next = prev.filter(s => s.id !== id)
      if (activeSessionId === id) {
        setActiveSessionId(next.length > 0 ? next[0].id : null)
      }
      return next
    })
  }, [activeSessionId])

  const sendMessage = useCallback(async (query: string) => {
    const validationError = validateQuery(query)
    if (validationError) {
      setInputError(validationError)
      return
    }
    setInputError(null)

    // Ensure we have an active session
    let currentSessionId = activeSessionId
    if (!currentSessionId) {
      currentSessionId = `chat-${Date.now()}`
      const newSession: ChatSession = {
        id: currentSessionId,
        title: query.substring(0, 30) + (query.length > 30 ? '...' : ''),
        updatedAt: Date.now(),
        messages: []
      }
      // Note: we'll add the message below so init with empty messages
      setSessions(prev => [newSession, ...prev])
      setActiveSessionId(currentSessionId)
    }

    const userMessage: ChatMessage = { id: nextId(), role: 'user', content: query.trim(), timestamp: now() }

    // Snapshot history before we add the user message to send to the backend
    let chat_history: any[] = [];
    setSessions(prev => {
      const s = prev.find(session => session.id === currentSessionId);
      if (s) {
        chat_history = s.messages.map(m => ({ role: m.role, content: m.content }));
      }
      return prev.map(session => {
        if (session.id === currentSessionId) {
          return {
            ...session,
            updatedAt: Date.now(),
            title: session.messages.length === 0 ? (query.substring(0, 30) + (query.length > 30 ? '...' : '')) : session.title,
            messages: [...session.messages, userMessage]
          }
        }
        return session
      })
    })

    setLoading(true)

    try {
      const data: AskResponse = await askQuestion(query.trim(), chat_history)

      const aiMessage: ChatMessage = {
        id: nextId(),
        role: 'assistant',
        content: data.answer,
        timestamp: now(),
        confidence: data.confidence,
        sources: data.sources,
      }

      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return { ...s, updatedAt: Date.now(), messages: [...s.messages, aiMessage] }
        }
        return s
      }))
    } catch (e) {
      const errorMessage: ChatMessage = {
        id: nextId(),
        role: 'error',
        content: e instanceof Error ? e.message : 'Unknown error',
        timestamp: now(),
      }
      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return { ...s, updatedAt: Date.now(), messages: [...s.messages, errorMessage] }
        }
        return s
      }))
    } finally {
      setLoading(false)
    }
  }, [activeSessionId])

  const clearChat = useCallback(() => {
    if (activeSessionId) {
      setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, messages: [], updatedAt: Date.now() } : s))
    }
  }, [activeSessionId])

  return {
    sessions,
    activeSessionId,
    messages,
    loading,
    inputError,
    sendMessage,
    clearChat,
    setInputError,
    createNewSession,
    switchSession,
    deleteSession
  }
}
