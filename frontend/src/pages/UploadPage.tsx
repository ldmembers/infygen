// pages/UploadPage.tsx

import Header from '@/components/layout/Header'
import UploadPanel from '@/components/upload/UploadPanel'

export default function UploadPage() {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header
        title="Documents"
        subtitle="Upload PDF, CSV and TXT files to your knowledge base"
      />
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto">
          {/* Info card */}
          <div className="mb-6 px-4 py-3 rounded-lg border border-border bg-surface">
            <div className="flex items-start gap-3">
              <span className="text-arc font-mono text-lg mt-0.5">⊞</span>
              <div>
                <p className="text-pale text-sm font-body">Files are processed through the ingestion pipeline:</p>
                <p className="text-ghost text-xs font-mono mt-1">
                  parse text → chunk → embed (nomic-embed-text) → store in FAISS index
                </p>
              </div>
            </div>
          </div>
          <UploadPanel />
        </div>
      </div>
    </div>
  )
}
