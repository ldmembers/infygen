// utils/validators.ts

const ALLOWED_EXTENSIONS = ['pdf', 'csv', 'txt']
const MAX_FILE_SIZE_MB   = 50

export function validateQuery(query: string): string | null {
  const q = query.trim()
  if (!q)         return 'Query cannot be empty.'
  if (q.length < 3)      return 'Query is too short (min 3 characters).'
  if (q.length > 2000)   return 'Query is too long (max 2000 characters).'
  return null
}

export function validateMemoryText(text: string): string | null {
  const t = text.trim()
  if (!t)         return 'Memory text cannot be empty.'
  if (t.length < 3)      return 'Memory is too short.'
  if (t.length > 5000)   return 'Memory is too long (max 5000 characters).'
  return null
}

export function validateFile(file: File): string | null {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `File type .${ext} is not allowed. Accepted: ${ALLOWED_EXTENSIONS.join(', ')}`
  }
  if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
    return `File "${file.name}" exceeds the ${MAX_FILE_SIZE_MB}MB limit.`
  }
  return null
}

export function validateFiles(files: File[]): string | null {
  if (files.length === 0) return 'Please select at least one file.'
  for (const f of files) {
    const err = validateFile(f)
    if (err) return err
  }
  return null
}
