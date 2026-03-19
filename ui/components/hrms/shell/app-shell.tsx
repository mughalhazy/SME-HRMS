'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Bell,
  BellRing,
  Building2,
  CalendarDays,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
  Users,
} from 'lucide-react'

import { useAuth } from '@/components/auth/auth-provider'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const navigationItems = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Employees', href: '/employees', icon: Users },
  { label: 'Attendance', href: '/attendance', icon: CalendarDays },
  { label: 'Leave', href: '/leave', icon: ClipboardList },
  { label: 'Payroll', href: '/payroll', icon: CreditCard },
  { label: 'Notifications', href: '/notifications', icon: BellRing },
  { label: 'Departments', href: '/departments', icon: Building2 },
  { label: 'Settings', href: '/settings', icon: Settings },
] as const

function isActiveRoute(pathname: string, href: string) {
  if (href === '/') {
    return pathname === '/'
  }

  return pathname === href || pathname.startsWith(`${href}/`)
}

function buildUserDisplay(session: ReturnType<typeof useAuth>['session']) {
  if (!session) {
    return {
      name: 'Secure user',
      subtitle: 'No active session',
      initials: 'SU',
    }
  }

  const username = session.user.employee_id ?? session.user.user_id
  const role = session.user.role
  return {
    name: username,
    subtitle: role,
    initials: role.slice(0, 2).toUpperCase(),
  }
}

type AppShellProps = {
  children: ReactNode
  pageTitle?: string
  pageDescription?: string
  pageActions?: ReactNode
}

export default function AppShell({
  children,
  pageTitle,
  pageDescription = 'Run daily HR operations from a consistent enterprise workspace.',
  pageActions,
}: AppShellProps) {
  const pathname = usePathname() ?? '/'
  const router = useRouter()
  const { session, logout } = useAuth()
  const activeItem = navigationItems.find((item) => isActiveRoute(pathname, item.href)) ?? navigationItems[0]
  const userDisplay = buildUserDisplay(session)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[272px] flex-col border-r border-slate-200 bg-white lg:flex">
        <div className="border-b border-slate-200 px-6 py-5">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-600 text-sm font-semibold text-white shadow-sm">
              HR
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-950">SME HRMS</p>
              <p className="truncate text-xs text-slate-500">Enterprise Workspace</p>
            </div>
          </Link>
        </div>

        <div className="flex flex-1 flex-col justify-between px-4 py-6">
          <nav className="space-y-1.5" aria-label="Primary navigation">
            {navigationItems.map((item) => {
              const active = isActiveRoute(pathname, item.href)
              const Icon = item.icon

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 rounded-2xl px-3.5 py-3 text-sm font-medium transition-colors hover:bg-gray-100',
                    active ? 'bg-blue-50 text-blue-600' : 'text-slate-600',
                  )}
                >
                  <span
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-xl transition-colors',
                      active ? 'bg-white text-blue-600 shadow-sm' : 'bg-slate-100 text-slate-500',
                    )}
                  >
                    <Icon className="h-4 w-4" />
                  </span>
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>

          <div className="space-y-4 border-t border-slate-200 pt-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center gap-3">
                <Avatar className="h-11 w-11 border border-slate-200 bg-white">
                  <AvatarFallback>{userDisplay.initials}</AvatarFallback>
                </Avatar>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-950">{userDisplay.name}</p>
                  <div className="mt-1 flex items-center gap-2">
                    <p className="truncate text-xs text-slate-500">{userDisplay.subtitle}</p>
                    <Badge variant="outline" className="gap-1 rounded-full px-2 py-0.5 text-[10px] uppercase tracking-[0.18em]">
                      <ShieldCheck className="h-3 w-3" />
                      Session active
                    </Badge>
                  </div>
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              className="w-full justify-start gap-3 rounded-xl px-3.5 text-slate-600 hover:bg-gray-100 hover:text-slate-900"
              onClick={async () => {
                await logout()
                router.replace('/login')
              }}
            >
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      <div className="lg:pl-[272px]">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="flex min-h-[76px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0 space-y-1">
              <h1 className="truncate text-2xl font-semibold tracking-tight text-slate-950">{pageTitle ?? activeItem.label}</h1>
              <p className="text-sm text-slate-500">{pageDescription}</p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center lg:justify-end">
              <div className="relative w-full sm:w-[320px]">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input className="border-slate-200 bg-white pl-9" placeholder="Search employees, payroll, or leave requests" />
              </div>
              <div className="flex items-center gap-3">
                <Link href="/notifications">
                  <Button variant="outline" size="icon" className="border-slate-200 bg-white hover:bg-slate-50" aria-label="Notifications">
                    <Bell className="h-4 w-4" />
                  </Button>
                </Link>
                {pageActions ?? null}
              </div>
            </div>
          </div>
        </header>

        <main className="min-h-[calc(100vh-76px)] bg-slate-50">
          <div className="mx-auto w-full max-w-[1600px] p-4 sm:p-6">{children}</div>
        </main>
      </div>
    </div>
  )
}

export { AppShell }
