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

type ApiRequestOptions = RequestInit & {
  headers?: HeadersInit
}

export function buildApiUrl(path: string) {
  return `${API_BASE_URL}${path}`
}

export function buildHeaders({ token, headers }: { token?: string; headers?: HeadersInit } = {}): HeadersInit {
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(headers ?? {}),
  }
}

export async function apiRequest<T>(path: string, init?: ApiRequestOptions): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: buildHeaders({ headers: init?.headers }),
  })

  const text = await response.text()

  if (!response.ok) {
    throw new Error(text || `API request failed with status ${response.status}`)
  }

  if (!text) {
    return undefined as T
  }

  return JSON.parse(text) as T
}
