'use client'

import { FormEvent, useState } from 'react'
import { useRouter } from 'next/navigation'

import { useAuth } from '@/components/auth/auth-provider'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ApiError } from '@/lib/api/client'

const DEMO_USERS = [
  { username: 'ava.manager', role: 'Manager' },
  { username: 'mika.admin', role: 'Admin' },
  { username: 'elliot.employee', role: 'Employee' },
] as const

export function LoginForm() {
  const router = useRouter()
  const { login } = useAuth()
  const [username, setUsername] = useState('ava.manager')
  const [password, setPassword] = useState('Password123!')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      await login({ username, password })
      router.replace('/dashboard')
    } catch (submitError) {
      setError(submitError instanceof ApiError ? submitError.message : 'Unable to sign in at the moment.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 bg-slate-950 lg:grid-cols-[minmax(0,1.1fr)_420px]">
      <section className="hidden flex-col justify-between border-r border-white/10 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.28),_transparent_45%),linear-gradient(180deg,_rgba(15,23,42,0.92),_rgba(2,6,23,1))] p-10 text-slate-100 lg:flex">
        <div className="space-y-5">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500 text-sm font-semibold text-white shadow-lg shadow-blue-950/30">HR</div>
          <div className="space-y-3">
            <p className="text-sm font-medium uppercase tracking-[0.28em] text-blue-200">SME HRMS</p>
            <h1 className="max-w-xl text-4xl font-semibold tracking-tight">Secure workforce operations with role-aware access, sessions, and short-lived tokens.</h1>
            <p className="max-w-lg text-base leading-7 text-slate-300">
              Sign in to manage employees, payroll, attendance, leave approvals, and performance workflows from one authenticated workspace.
            </p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {DEMO_USERS.map((user) => (
            <button
              key={user.username}
              type="button"
              onClick={() => {
                setUsername(user.username)
                setPassword('Password123!')
              }}
              className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-blue-300/40 hover:bg-white/10"
            >
              <p className="text-sm font-semibold text-white">{user.username}</p>
              <p className="mt-1 text-xs text-slate-300">{user.role} demo account</p>
            </button>
          ))}
        </div>
      </section>

      <section className="flex items-center justify-center p-6 sm:p-10">
        <Card className="w-full max-w-md border-white/10 bg-white shadow-2xl shadow-slate-950/25">
          <CardHeader className="space-y-2">
            <CardTitle className="text-2xl">Log in</CardTitle>
            <CardDescription>Use your SME HRMS credentials to start a new authenticated session.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={onSubmit}>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="username">
                  Username
                </label>
                <Input id="username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700" htmlFor="password">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>

              {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? 'Signing in…' : 'Sign in'}
              </Button>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-6 text-slate-500">
                <p className="font-semibold text-slate-700">Demo password</p>
                <p>Password123!</p>
              </div>
            </form>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
