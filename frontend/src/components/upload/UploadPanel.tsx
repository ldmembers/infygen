// components/upload/UploadPanel.tsx

import { useState, useRef, type DragEvent, type ChangeEvent } from 'react'
import { uploadFiles } from '@/services/uploadService'
import { validateFiles } from '@/utils/validators'
import FileList, { type FileItem } from './FileList'
import Toast from '@/components/ui/Toast'

export default function UploadPanel() {
  const [fileItems, setFileItems]     = useState<FileItem[]>([])
  const [progress,  setProgress]      = useState<number>(0)
  const [dragging,  setDragging]      = useState(false)
  const [toast,     setToast]         = useState<{ msg: string; type: 'success' | 'error' | 'info' } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function addFiles(newFiles: File[]) {
    const validErr = validateFiles(newFiles)
    if (validErr) {
      setToast({ msg: validErr, type: 'error' })
      return
    }
    setFileItems(newFiles.map((f) => ({ name: f.name, size: f.size, status: 'pending' })))
    setToast(null)
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault(); setDragging(false)
    addFiles(Array.from(e.dataTransfer.files))
  }

  function handleSelect(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) addFiles(Array.from(e.target.files))
  }

  async function handleUpload() {
    const files = fileItems.filter((f) => f.status !== 'success')
    if (files.length === 0) return

    // Mark all as uploading
    setFileItems((prev) => prev.map((f) => ({ ...f, status: 'uploading' as const })))
    setProgress(0)

    // Reconstruct File objects — we only have metadata, so re-select from input
    const inputFiles = Array.from(inputRef.current?.files ?? [])

    try {
      const res = await uploadFiles(inputFiles, setProgress)

      setFileItems((prev) =>
        prev.map((f) => {
          const ok  = res.uploaded.find((u) => u.file === f.name)
          const err = res.failed.find((u) => u.file === f.name)
          if (ok)  return { ...f, status: 'success', chunks: ok.chunks }
          if (err) return { ...f, status: 'error',   message: err.error }
          return f
        })
      )

      if (res.total_failed === 0) {
        setToast({ msg: `Successfully indexed ${res.total_uploaded} file(s).`, type: 'success' })
      } else {
        setToast({ msg: `${res.total_uploaded} uploaded, ${res.total_failed} failed.`, type: 'error' })
      }
    } catch (e) {
      setFileItems((prev) => prev.map((f) => ({ ...f, status: 'error', message: e instanceof Error ? e.message : 'Upload failed' })))
      setToast({ msg: e instanceof Error ? e.message : 'Upload failed', type: 'error' })
    }
  }

  const hasPending = fileItems.some((f) => f.status === 'pending')

  return (
    <div className="space-y-4">
      {toast && <Toast message={toast.msg} type={toast.type} onDismiss={() => setToast(null)} />}

      {/* Drop zone */}
      <div
        onDragEnter={() => setDragging(true)}
        onDragLeave={() => setDragging(false)}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className="relative border-2 border-dashed rounded-xl px-8 py-12 flex flex-col items-center justify-center cursor-pointer transition-all duration-200"
        style={{
          borderColor: dragging ? 'rgba(74,244,200,0.6)' : 'rgba(74,244,200,0.15)',
          background:  dragging ? 'rgba(74,244,200,0.03)' : 'transparent',
        }}
      >
        <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
          style={{ background: 'rgba(74,244,200,0.08)', border: '1px solid rgba(74,244,200,0.2)' }}>
          <svg className="w-5 h-5 text-arc" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
          </svg>
        </div>
        <p className="text-pale text-sm font-body font-medium mb-1">Drop files here or click to browse</p>
        <p className="text-ghost text-xs font-mono">PDF · CSV · TXT  ·  max 50 MB each</p>

        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.csv,.txt"
          onChange={handleSelect}
          className="hidden"
        />
      </div>

      {/* File list */}
      <FileList files={fileItems} />

      {/* Progress bar */}
      {progress > 0 && progress < 100 && (
        <div className="h-1 rounded-full bg-muted overflow-hidden">
          <div className="h-full bg-arc rounded-full conf-fill" style={{ width: `${progress}%` }} />
        </div>
      )}

      {/* Upload button */}
      {hasPending && (
        <button onClick={handleUpload} className="btn-arc w-full justify-center flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
          </svg>
          Index {fileItems.filter((f) => f.status === 'pending').length} file(s)
        </button>
      )}
    </div>
  )
}
