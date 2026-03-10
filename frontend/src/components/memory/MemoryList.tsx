// components/memory/MemoryList.tsx

interface MemoryItem { content: string; storedAt: string }
interface Props { items: MemoryItem[] }

export default function MemoryList({ items }: Props) {
  if (items.length === 0) return (
    <div className="text-center py-8 text-ghost text-sm font-mono opacity-50">
      No memories stored yet in this session.
    </div>
  )

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div key={i} className="flex gap-3 px-4 py-3 rounded-lg border border-border bg-surface animate-fade-up">
          <div className="w-1.5 flex-shrink-0 rounded-full mt-1" style={{ background: '#ffc864', minHeight: '1rem' }} />
          <div className="flex-1 min-w-0">
            <p className="text-pale text-sm font-body leading-relaxed">{item.content}</p>
            <p className="text-ghost text-[10px] font-mono mt-1">{item.storedAt}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

export type { MemoryItem }
