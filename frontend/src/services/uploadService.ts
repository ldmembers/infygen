// services/uploadService.ts
// Handles POST /upload with multipart form data and progress tracking.

import apiClient from './apiClient'
import { ENDPOINTS } from '@/config/api'

export interface UploadResult {
  file:          string
  status:        'ok' | 'error'
  chunks?:       number
  elapsed_sec?:  number
  error?:        string
}

export interface UploadResponse {
  uploaded:       UploadResult[]
  failed:         UploadResult[]
  total_uploaded: number
  total_failed:   number
}

export async function uploadFiles(
  files: File[],
  onProgress?: (pct: number) => void
): Promise<UploadResponse> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))

  const { data } = await apiClient.post<UploadResponse>(ENDPOINTS.upload, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
  return data
}
