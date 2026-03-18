const env = (globalThis as typeof globalThis & { process?: { env?: Record<string, string | undefined> } }).process?.env
const API_BASE_URL = env?.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status?: number
  payload?: unknown

  constructor(message: string, options?: { status?: number; payload?: unknown }) {
    super(message)
    this.name = 'ApiError'
    this.status = options?.status
    this.payload = options?.payload
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  const text = await response.text()
  let payload: unknown = null

  if (text) {
    try {
      payload = JSON.parse(text) as unknown
    } catch {
      payload = text
    }
  }

  if (!response.ok) {
    throw new ApiError(`API request failed with status ${response.status}`, {
      status: response.status,
      payload,
    })
  }

  return payload as T
}
