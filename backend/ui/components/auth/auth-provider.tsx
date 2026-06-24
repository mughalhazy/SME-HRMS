'use client'

import type { ReactNode } from 'react'
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

import { ApiError, registerAccessTokenResolver } from '@/lib/api/client'
import { loginRequest, logoutRequest, refreshSessionRequest } from '@/lib/auth/api'
import {
  AuthSession,
  AUTH_STORAGE_KEY,
  isAccessTokenExpired,
  isRefreshTokenExpired,
  persistSession,
  readStoredSession,
} from '@/lib/auth/session'

type LoginInput = {
  username: string
  password: string
}

type AuthContextValue = {
  isReady: boolean
  isAuthenticated: boolean
  session: AuthSession | null
  accessToken: string | null
  login: (input: LoginInput) => Promise<void>
  logout: () => Promise<void>
  getValidAccessToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function isSessionStillUsable(session: AuthSession) {
  return !isRefreshTokenExpired(session)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false)
  const [session, setSession] = useState<AuthSession | null>(null)
  const refreshPromiseRef = useRef<Promise<string | null> | null>(null)

  const commitSession = useCallback((nextSession: AuthSession | null) => {
    setSession(nextSession)
    persistSession(nextSession)
  }, [])

  useEffect(() => {
    const stored = readStoredSession()
    if (stored && isSessionStillUsable(stored)) {
      setSession(stored)
    } else {
      persistSession(null)
    }
    setIsReady(true)
  }, [])

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== AUTH_STORAGE_KEY) {
        return
      }

      const stored = readStoredSession()
      setSession(stored && isSessionStillUsable(stored) ? stored : null)
    }

    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const login = useCallback(async ({ username, password }: LoginInput) => {
    const nextSession = await loginRequest({ username, password })
    commitSession(nextSession)
  }, [commitSession])

  const logout = useCallback(async () => {
    const refreshToken = session?.tokens.refresh_token
    commitSession(null)
    if (refreshToken) {
      await logoutRequest(refreshToken)
    }
  }, [commitSession, session?.tokens.refresh_token])

  const getValidAccessToken = useCallback(async () => {
    if (!session) {
      return null
    }

    if (!isAccessTokenExpired(session)) {
      return session.tokens.access_token
    }

    if (isRefreshTokenExpired(session)) {
      commitSession(null)
      return null
    }

    if (!refreshPromiseRef.current) {
      refreshPromiseRef.current = refreshSessionRequest(session.tokens.refresh_token)
        .then((nextSession) => {
          commitSession(nextSession)
          return nextSession.tokens.access_token
        })
        .catch((error) => {
          commitSession(null)
          if (error instanceof ApiError) {
            return null
          }
          throw error
        })
        .finally(() => {
          refreshPromiseRef.current = null
        })
    }

    return refreshPromiseRef.current
  }, [commitSession, session])

  useEffect(() => {
    registerAccessTokenResolver(() => getValidAccessToken())
    return () => registerAccessTokenResolver(null)
  }, [getValidAccessToken])

  const value = useMemo<AuthContextValue>(
    () => ({
      isReady,
      isAuthenticated: Boolean(session),
      session,
      accessToken: session?.tokens.access_token ?? null,
      login,
      logout,
      getValidAccessToken,
    }),
    [getValidAccessToken, isReady, login, logout, session],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
