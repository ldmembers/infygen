// components/upload/FileList.tsx

interface FileItem {
  name:    string
  size:    number
  status:  'pending' | 'uploading' | 'success' | 'error'
  message?: string
  chunks?:  number
}

interface Props { files: FileItem[] }

const EXT_COLORS: Record<string, string> = {
  pdf: '#6b8cff', csv: '#4af4c8', txt: '#f4804a',
}

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  return ext.toUpperCase()
}

function fileColor(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  return EXT_COLORS[ext] ?? '#8892a4'
}

function formatSize(bytes: number) {
  if (bytes < 1024)        return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default function FileList({ files }: Props) {
  if (files.length === 0) return null

  return (
    <div className="space-y-2">
      {files.map((f, i) => {
        const color = fileColor(f.name)
        return (
          <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-lg border border-border bg-surface animate-fade-up">
            {/* File type badge */}
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-[9px] font-mono font-bold flex-shrink-0"
              style={{ background: `${color}11`, border: `1px solid ${color}33`, color }}
            >
              {fileIcon(f.name)}
            </div>

            {/* Name + size */}
            <div className="flex-1 min-w-0">
              <div className="text-pale text-sm font-body truncate">{f.name}</div>
              <div className="text-ghost text-[10px] font-mono">{formatSize(f.size)}</div>
            </div>

            {/* Status */}
            <div className="flex-shrink-0">
              {f.status === 'pending' && (
                <span className="text-ghost text-[10px] font-mono">queued</span>
              )}
              {f.status === 'uploading' && (
                <svg className="animate-spin w-4 h-4 text-arc" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
              )}
              {f.status === 'success' && (
                <div className="flex items-center gap-1.5">
                  {f.chunks && <span className="text-arc/60 text-[10px] font-mono">{f.chunks} chunks</span>}
                  <span className="text-arc text-base">✓</span>
                </div>
              )}
              {f.status === 'error' && (
                <span className="text-ember text-sm" title={f.message}>✕</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export type { FileItem }
