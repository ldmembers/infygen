// config/api.ts — Centralised API configuration

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const ENDPOINTS = {
  ask: `${API_BASE_URL}/ask`,
  upload: `${API_BASE_URL}/upload`,
  remember: `${API_BASE_URL}/remember`,
  gmailAuth: `${API_BASE_URL}/gmail/auth`,       // GET → redirects to Google
  gmailSync: `${API_BASE_URL}/gmail/sync`,        // POST → manual re-sync
  gmailStatus: `${API_BASE_URL}/gmail/status`,      // GET → connection + doc counts
  driveFiles: `${API_BASE_URL}/drive/files`,       // GET → indexed file list
  driveSync: `${API_BASE_URL}/drive/sync`,        // POST → manual re-sync
  timeline: `${API_BASE_URL}/timeline`,
  health: `${API_BASE_URL}/health`,
} as const
