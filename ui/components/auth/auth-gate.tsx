'use client'

import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'

import { useAuth } from '@/components/auth/auth-provider'

const PUBLIC_PATHS = new Set(['/login'])

export function AuthGate({ children }: { children: ReactNode }) {
  const pathname = usePathname() ?? '/'
  const router = useRouter()
  const { isReady, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isReady) {
      return
    }

    const isPublic = PUBLIC_PATHS.has(pathname)
    if (!isAuthenticated && !isPublic) {
      router.replace('/login')
      return
    }

    if (isAuthenticated && isPublic) {
      router.replace('/')
    }
  }, [isAuthenticated, isReady, pathname, router])

  if (!isReady) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">Loading secure workspace…</div>
  }

  const isPublic = PUBLIC_PATHS.has(pathname)
  if (!isAuthenticated && !isPublic) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">Redirecting to login…</div>
  }

  if (isAuthenticated && isPublic) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">Loading secure workspace…</div>
  }

  return <>{children}</>
}
