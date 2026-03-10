// utils/errorHandler.ts
// Normalises Axios / Firebase errors into user-friendly strings.

import type { AxiosError } from 'axios'

interface ApiErrorBody {
  error?:  string
  detail?: string
}

export function normaliseError(error: unknown): string {
  // Axios errors with a JSON response body
  if (isAxiosError(error)) {
    const data = error.response?.data as ApiErrorBody | undefined
    if (data?.error)  return data.error
    if (data?.detail) return data.detail

    switch (error.response?.status) {
      case 401: return 'Authentication required. Please log in again.'
      case 403: return 'Access denied.'
      case 404: return 'Resource not found.'
      case 413: return 'File is too large.'
      case 422: return 'Invalid input. Please check your request.'
      case 503: return 'AI service is temporarily unavailable. Check that Ollama is running.'
      default:  return `Server error (${error.response?.status ?? 'unknown'})`
    }
  }

  // Network errors (no response)
  if (error instanceof Error) {
    if (error.message.includes('Network Error') || error.message.includes('ECONNREFUSED')) {
      return 'Cannot reach the backend. Make sure uvicorn is running on port 8000.'
    }
    return error.message
  }

  return 'An unexpected error occurred.'
}

function isAxiosError(e: unknown): e is AxiosError {
  return typeof e === 'object' && e !== null && 'isAxiosError' in e
}
