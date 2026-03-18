const env = (globalThis as typeof globalThis & { process?: { env?: Record<string, string | undefined> } }).process?.env
const API_BASE_URL = env?.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export type ApiErrorDetail = {
  field?: string
  reason?: string
}

export class ApiError extends Error {
  status?: number
  code?: string
  payload?: unknown
  traceId?: string
  details: ApiErrorDetail[]

  constructor(message: string, options?: { status?: number; code?: string; payload?: unknown; traceId?: string; details?: ApiErrorDetail[] }) {
    super(message)
    this.name = 'ApiError'
    this.status = options?.status
    this.code = options?.code
    this.payload = options?.payload
    this.traceId = options?.traceId
    this.details = options?.details ?? []
  }
}

type ApiRequestOptions = RequestInit & {
  headers?: HeadersInit
}

type ErrorEnvelope = {
  error?: {
    code?: string
    message?: string
    details?: ApiErrorDetail[]
    traceId?: string
  }
}

export function buildApiUrl(path: string) {
  return `${API_BASE_URL}${path}`
}

export function buildHeaders({ token, headers, hasJsonBody = true }: { token?: string; headers?: HeadersInit; hasJsonBody?: boolean } = {}): HeadersInit {
  return {
    ...(hasJsonBody ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(headers ?? {}),
  }
}

function parseJsonSafely(text: string): unknown {
  if (!text) {
    return undefined
  }

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function apiRequest<T>(path: string, init?: ApiRequestOptions): Promise<T> {
  const hasJsonBody = !(init?.body instanceof FormData)

  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: buildHeaders({ headers: init?.headers, hasJsonBody }),
  })

  const text = await response.text()
  const payload = parseJsonSafely(text)

  if (!response.ok) {
    const envelope = (payload && typeof payload === 'object' ? payload : undefined) as ErrorEnvelope | undefined
    throw new ApiError(envelope?.error?.message ?? (typeof payload === 'string' ? payload : `API request failed with status ${response.status}`), {
      status: response.status,
      code: envelope?.error?.code,
      payload,
      traceId: envelope?.error?.traceId,
      details: envelope?.error?.details ?? [],
    })
  }

  if (!text) {
    return undefined as T
  }

  return payload as T
}
