// services/memoryService.ts
// Handles POST /remember — storing personal memories.

import apiClient from './apiClient'
import { ENDPOINTS } from '@/config/api'

export interface MemoryResponse {
  stored:  boolean
  content: string
  message: string
}

export async function storeMemory(text: string): Promise<MemoryResponse> {
  const { data } = await apiClient.post<MemoryResponse>(ENDPOINTS.remember, { text })
  return data
}
