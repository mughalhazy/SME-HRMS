import { apiRequest, ApiError } from '@/lib/api/client'
import { AuthSession, AuthUser, SessionTokens, createSession } from '@/lib/auth/session'

type LoginResponse = {
  data: SessionTokens
}

type MeResponse = {
  data: AuthUser
}

export async function loginRequest(credentials: { username: string; password: string }): Promise<AuthSession> {
  const login = await apiRequest<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
    skipAuth: true,
  })

  const me = await apiRequest<MeResponse>('/api/v1/auth/me', {
    skipAuth: true,
    headers: {
      Authorization: `Bearer ${login.data.access_token}`,
    },
  })

  return createSession(me.data, login.data)
}

export async function refreshSessionRequest(refreshToken: string): Promise<AuthSession> {
  const refresh = await apiRequest<LoginResponse>('/api/v1/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
    skipAuth: true,
  })

  const me = await apiRequest<MeResponse>('/api/v1/auth/me', {
    skipAuth: true,
    headers: {
      Authorization: `Bearer ${refresh.data.access_token}`,
    },
  })

  return createSession(me.data, refresh.data)
}

export async function logoutRequest(refreshToken: string): Promise<void> {
  try {
    await apiRequest('/api/v1/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
      skipAuth: true,
    })
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return
    }

    throw error
  }
}
