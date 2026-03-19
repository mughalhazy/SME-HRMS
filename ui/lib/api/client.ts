import { mockApiRequest } from '@/lib/api/mock'

const env = (globalThis as typeof globalThis & { process?: { env?: Record<string, string | undefined> } }).process?.env
const API_BASE_URL = env?.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
export const USE_MOCK = (env?.NEXT_PUBLIC_USE_MOCK ?? env?.USE_MOCK ?? 'true').toLowerCase() === 'true'

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
  skipAuth?: boolean
}

type ErrorEnvelope = {
  error?: {
    code?: string
    message?: string
    details?: ApiErrorDetail[]
    traceId?: string
  }
}

type AccessTokenResolver = () => Promise<string | null> | string | null

let accessTokenResolver: AccessTokenResolver | null = null

export function registerAccessTokenResolver(resolver: AccessTokenResolver | null) {
  accessTokenResolver = resolver
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

async function resolveAccessToken(skipAuth?: boolean) {
  if (skipAuth || !accessTokenResolver) {
    return undefined
  }

  return (await accessTokenResolver()) ?? undefined
}

export async function apiRequest<T>(path: string, init?: ApiRequestOptions): Promise<T> {
  const hasJsonBody = !(init?.body instanceof FormData)
  const token = await resolveAccessToken(init?.skipAuth)
  const headers = buildHeaders({ token, headers: init?.headers, hasJsonBody })

  if (USE_MOCK) {
    try {
      return await mockApiRequest<T>(path, {
        ...init,
        headers,
      })
    } catch (error) {
      throw error instanceof ApiError
        ? error
        : new ApiError(error instanceof Error ? error.message : 'Mock API request failed', {
            status: 503,
            payload: error,
          })
    }
  }

  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers,
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
