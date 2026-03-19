export type AuthUser = {
  user_id: string
  employee_id: string | null
  role: string
  department_id: string | null
}

export type SessionTokens = {
  access_token: string
  refresh_token: string
  token_type: 'Bearer'
  expires_in: number
  refresh_expires_in: number
  session_id: string
}

export type AuthSession = {
  user: AuthUser
  tokens: SessionTokens
  expires_at: number
  refresh_expires_at: number
}

export const AUTH_STORAGE_KEY = 'sme-hrms.auth.session'

export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split('.')
  if (parts.length !== 3) {
    return null
  }

  try {
    const segment = parts[1]
    const padded = segment.padEnd(segment.length + ((4 - (segment.length % 4)) % 4), '=')
    const normalized = padded.replace(/-/g, '+').replace(/_/g, '/')
    const json = globalThis.atob(normalized)
    return JSON.parse(json) as Record<string, unknown>
  } catch {
    return null
  }
}

export function createSession(user: AuthUser, tokens: SessionTokens): AuthSession {
  const now = Date.now()
  return {
    user,
    tokens,
    expires_at: now + tokens.expires_in * 1000,
    refresh_expires_at: now + tokens.refresh_expires_in * 1000,
  }
}

export function readStoredSession(): AuthSession | null {
  if (typeof window === 'undefined') {
    return null
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as AuthSession
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export function persistSession(session: AuthSession | null) {
  if (typeof window === 'undefined') {
    return
  }

  if (!session) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    return
  }

  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function isAccessTokenExpired(session: AuthSession, skewMs = 30_000) {
  return session.expires_at <= Date.now() + skewMs
}

export function isRefreshTokenExpired(session: AuthSession, skewMs = 30_000) {
  return session.refresh_expires_at <= Date.now() + skewMs
}
