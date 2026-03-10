// components/memory/MemoryForm.tsx

import { useState } from 'react'
import { storeMemory } from '@/services/memoryService'
import { validateMemoryText } from '@/utils/validators'
import Toast from '@/components/ui/Toast'

interface Props { onStored?: (text: string) => void }

export default function MemoryForm({ onStored }: Props) {
  const [text,    setText]    = useState('')
  const [loading, setLoading] = useState(false)
  const [toast,   setToast]   = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

  async function handleSubmit() {
    const err = validateMemoryText(text)
    if (err) { setToast({ msg: err, type: 'error' }); return }

    setLoading(true)
    try {
      const res = await storeMemory(text.trim())
      setToast({ msg: res.message, type: 'success' })
      onStored?.(text.trim())
      setText('')
    } catch (e) {
      setToast({ msg: e instanceof Error ? e.message : 'Failed to store memory', type: 'error' })
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-3">
      {toast && <Toast message={toast.msg} type={toast.type} onDismiss={() => setToast(null)} />}

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={"Remember that catering vendor is ABC Foods.\nDecided to use two buses for transport."}
        rows={4}
        className="input-field resize-none leading-relaxed"
      />

      <button
        onClick={handleSubmit}
        disabled={!text.trim() || loading}
        className="btn-arc flex items-center gap-2"
      >
        {loading ? (
          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
        ) : (
          <span className="font-mono text-base">◎</span>
        )}
        {loading ? 'Storing…' : 'Store Memory'}
      </button>
    </div>
  )
}
