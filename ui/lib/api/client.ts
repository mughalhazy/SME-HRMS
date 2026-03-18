const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN

export interface ApiErrorDetail {
  field?: string
  reason?: string
}

export class ApiError extends Error {
  status: number
  code?: string
  details: ApiErrorDetail[]
  traceId?: string

  constructor(status: number, message: string, options?: { code?: string; details?: ApiErrorDetail[]; traceId?: string }) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = options?.code
    this.details = options?.details ?? []
    this.traceId = options?.traceId
  }
}

function buildHeaders(init?: RequestInit): Headers {
  const headers = new Headers(init?.headers)

  if (!headers.has('Content-Type') && init?.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (API_TOKEN && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${API_TOKEN}`)
  }

  return headers
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: buildHeaders(init),
    cache: init?.cache ?? 'no-store',
  })

  if (!response.ok) {
    let message = `API request failed with status ${response.status}`
    let code: string | undefined
    let details: ApiErrorDetail[] = []
    let traceId: string | undefined

    try {
      const payload = (await response.json()) as {
        error?: {
          code?: string
          message?: string
          details?: ApiErrorDetail[]
          traceId?: string
        }
      }

      if (payload.error) {
        message = payload.error.message ?? message
        code = payload.error.code
        details = payload.error.details ?? []
        traceId = payload.error.traceId
      }
    } catch {
      // Ignore JSON parsing failures and surface the default error.
    }

    throw new ApiError(response.status, message, { code, details, traceId })
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
