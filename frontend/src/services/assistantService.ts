// services/assistantService.ts
// Handles POST /ask — querying the AI assistant.

import apiClient from './apiClient'
import { ENDPOINTS } from '@/config/api'

export interface AskResponse {
  answer: string
  confidence: string   // e.g. "87%"
  sources: string[]
  result_count: number
}

export async function askQuestion(query: string, chat_history: any[] = []): Promise<AskResponse> {
  const { data } = await apiClient.post<AskResponse>(ENDPOINTS.ask, { query, chat_history })
  return data
}
