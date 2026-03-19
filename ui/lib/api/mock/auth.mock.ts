import { ApiError } from '@/lib/api/client'
import { decodeJwtPayload, type AuthUser, type SessionTokens } from '@/lib/auth/session'

type DemoUser = AuthUser & {
  username: string
  password: string
}

type DemoSession = {
  session_id: string
  user_id: string
  refresh_token: string
  refresh_expires_at: number
  revoked: boolean
}

const ACCESS_TTL_SECONDS = 15 * 60
const REFRESH_TTL_SECONDS = 7 * 24 * 60 * 60
const ISSUER = 'sme-hrms.auth-service'
const AUDIENCE = 'sme-hrms.api'

const users: DemoUser[] = [
  {
    username: 'ava.manager',
    password: 'Password123!',
    user_id: 'user-manager-001',
    employee_id: 'emp-006',
    role: 'Manager',
    department_id: 'dep-hr',
  },
  {
    username: 'mika.admin',
    password: 'Password123!',
    user_id: 'user-admin-001',
    employee_id: 'emp-010',
    role: 'Admin',
    department_id: null,
  },
  {
    username: 'elliot.employee',
    password: 'Password123!',
    user_id: 'user-employee-001',
    employee_id: 'emp-003',
    role: 'Employee',
    department_id: 'dep-eng',
  },
]

const sessions = new Map<string, DemoSession>()

function encodeSegment(value: unknown) {
  return btoa(JSON.stringify(value)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function createAccessToken(user: DemoUser, sessionId: string) {
  const now = Math.floor(Date.now() / 1000)
  return `${encodeSegment({ alg: 'none', typ: 'JWT' })}.${encodeSegment({
    sub: user.user_id,
    sid: sessionId,
    role: user.role,
    employee_id: user.employee_id,
    department_id: user.department_id,
    iat: now,
    nbf: now,
    exp: now + ACCESS_TTL_SECONDS,
    iss: ISSUER,
    aud: AUDIENCE,
  })}.mock-signature`
}

function issueTokens(user: DemoUser, sessionId = crypto.randomUUID()): SessionTokens {
  const refresh_token = crypto.randomUUID()
  sessions.set(sessionId, {
    session_id: sessionId,
    user_id: user.user_id,
    refresh_token,
    refresh_expires_at: Date.now() + REFRESH_TTL_SECONDS * 1000,
    revoked: false,
  })

  return {
    access_token: createAccessToken(user, sessionId),
    refresh_token,
    token_type: 'Bearer',
    expires_in: ACCESS_TTL_SECONDS,
    refresh_expires_in: REFRESH_TTL_SECONDS,
    session_id: sessionId,
  }
}

function getUserFromAccessToken(authorization?: string | null) {
  if (!authorization?.startsWith('Bearer ')) {
    throw new ApiError('Missing bearer token', { status: 401, code: 'TOKEN_INVALID' })
  }

  const payload = decodeJwtPayload(authorization.slice(7))
  if (!payload) {
    throw new ApiError('Malformed token', { status: 401, code: 'TOKEN_INVALID' })
  }

  const sessionId = typeof payload.sid === 'string' ? payload.sid : null
  const userId = typeof payload.sub === 'string' ? payload.sub : null
  const exp = typeof payload.exp === 'number' ? payload.exp : 0
  if (!sessionId || !userId || exp * 1000 <= Date.now()) {
    throw new ApiError('Token has expired', { status: 401, code: 'TOKEN_EXPIRED' })
  }

  const session = sessions.get(sessionId)
  if (!session || session.revoked || session.user_id !== userId) {
    throw new ApiError('Session has been revoked', { status: 401, code: 'TOKEN_REVOKED' })
  }

  const user = users.find((candidate) => candidate.user_id === userId)
  if (!user) {
    throw new ApiError('User not found', { status: 401, code: 'TOKEN_INVALID' })
  }

  return user
}

export async function loginMock(body: { username?: unknown; password?: unknown }) {
  const username = typeof body.username === 'string' ? body.username.trim().toLowerCase() : ''
  const password = typeof body.password === 'string' ? body.password : ''
  const user = users.find((candidate) => candidate.username === username)
  if (!user || user.password !== password) {
    throw new ApiError('Invalid username or password', { status: 401, code: 'INVALID_CREDENTIALS' })
  }

  return { data: issueTokens(user) }
}

export async function meMock(headers?: HeadersInit) {
  const authorization = new Headers(headers).get('Authorization')
  const user = getUserFromAccessToken(authorization)
  return {
    data: {
      user_id: user.user_id,
      employee_id: user.employee_id,
      role: user.role,
      department_id: user.department_id,
    },
  }
}

export async function refreshMock(body: { refresh_token?: unknown }) {
  const refreshToken = typeof body.refresh_token === 'string' ? body.refresh_token : ''
  const session = [...sessions.values()].find((candidate) => candidate.refresh_token === refreshToken)
  if (!session || session.revoked || session.refresh_expires_at <= Date.now()) {
    throw new ApiError('Refresh token is invalid or expired', { status: 401, code: 'TOKEN_INVALID' })
  }

  const user = users.find((candidate) => candidate.user_id === session.user_id)
  if (!user) {
    throw new ApiError('User not found', { status: 401, code: 'TOKEN_INVALID' })
  }

  session.revoked = true
  return { data: issueTokens(user) }
}

export async function logoutMock(body: { refresh_token?: unknown }) {
  const refreshToken = typeof body.refresh_token === 'string' ? body.refresh_token : ''
  const session = [...sessions.values()].find((candidate) => candidate.refresh_token === refreshToken)
  if (session) {
    session.revoked = true
  }
  return { data: { logged_out: true } }
}
