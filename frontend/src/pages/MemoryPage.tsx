// pages/MemoryPage.tsx

import { useState } from 'react'
import Header from '@/components/layout/Header'
import MemoryForm from '@/components/memory/MemoryForm'
import MemoryList, { type MemoryItem } from '@/components/memory/MemoryList'

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([])

  function handleStored(content: string) {
    setMemories((prev) => [
      { content, storedAt: new Date().toLocaleString() },
      ...prev,
    ])
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Memory"
        subtitle="Store facts and decisions for the assistant to recall"
      />
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Store form */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-amber-400 font-mono">◎</span>
              <h3 className="font-display text-snow text-sm font-semibold">Store a memory</h3>
            </div>
            <MemoryForm onStored={handleStored} />
          </div>

          {/* Examples */}
          <div className="px-4 py-3 rounded-lg border border-border bg-surface">
            <p className="text-ghost text-xs font-mono mb-2 uppercase tracking-wider">Example memories</p>
            {[
              'The catering vendor is ABC Foods. Contact Sarah at 555-0101.',
              'Transport for the event will use two City Travels buses.',
              'Project deadline is March 15, 2025.',
            ].map((ex) => (
              <p key={ex} className="text-ghost text-xs font-body leading-relaxed mb-1">
                · {ex}
              </p>
            ))}
          </div>

          {/* Stored list (this session) */}
          {memories.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-ghost text-xs font-mono uppercase tracking-wider">Stored this session</span>
                <span className="text-arc font-mono text-xs">{memories.length}</span>
              </div>
              <MemoryList items={memories} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
