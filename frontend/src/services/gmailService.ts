// services/gmailService.ts
// Gmail OAuth & sync — calls backend API with auth token, then redirects to Google.

import apiClient from './apiClient'

export interface GmailStatus {
  connected: boolean
  last_synced: string | null
  emails_indexed: number
  drive_docs_indexed: number
  sheets_indexed: number
}

export interface GmailSyncResponse {
  indexed: number
  chunks_stored: number
  message: string
}

/**
 * Start Gmail OAuth:
 * 1. Call /gmail/auth API (with Firebase JWT) → get Google OAuth URL
 * 2. Redirect browser to Google's consent screen
 * The backend callback will redirect back to /gmail?connected=true
 */
export async function startGmailOAuth(): Promise<void> {
  const { data } = await apiClient.get<{ auth_url: string }>('/gmail/auth')
  if (!data.auth_url) throw new Error('No auth_url returned from server')
  window.location.href = data.auth_url
}

export async function getGmailStatus(): Promise<GmailStatus> {
  const { data } = await apiClient.get<GmailStatus>('/gmail/status')
  return data
}

export async function syncGmail(maxEmails = 50): Promise<GmailSyncResponse> {
  const { data } = await apiClient.post<GmailSyncResponse>('/gmail/sync', {
    max_emails: maxEmails,
  })
  return data
}

export interface IndexedFile {
  id: number
  name: string
  document_id: string
  indexed_at: string
  status: string
}

export async function getGmailFiles(): Promise<IndexedFile[]> {
  const { data } = await apiClient.get<IndexedFile[]>('/gmail/files')
  return data
}

export async function getDriveFiles(): Promise<IndexedFile[]> {
  const { data } = await apiClient.get<IndexedFile[]>('/drive/files')
  return data
}
