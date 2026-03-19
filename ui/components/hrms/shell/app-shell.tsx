'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Bell,
  CalendarDays,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Search,
  Settings,
  Trees,
  Users,
} from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const navigationItems = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Employees', href: '/employees', icon: Users },
  { label: 'Attendance', href: '/attendance', icon: CalendarDays },
  { label: 'Leave', href: '/leave', icon: ClipboardList },
  { label: 'Payroll', href: '/payroll', icon: CreditCard },
  { label: 'Departments', href: '/departments', icon: Trees },
  { label: 'Settings', href: '/settings', icon: Settings },
] as const

function isActiveRoute(pathname: string, href: string) {
  if (href === '/') {
    return pathname === '/'
  }

  return pathname === href || pathname.startsWith(`${href}/`)
}

interface AppShellProps {
  children: ReactNode
  pageTitle?: string
}

export function AppShell({ children, pageTitle = 'Workspace Overview' }: AppShellProps) {
  const pathname = usePathname() ?? '/'

  return (
    <div className="h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 z-30 flex w-[260px] flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-6 py-5">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-sm font-semibold text-white">
              HR
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-950">HRMS</p>
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
                    'flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium transition-colors',
                    active
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                  )}
                >
                  <span
                    className={cn(
                      'flex h-9 w-9 items-center justify-center rounded-lg',
                      active ? 'bg-white text-blue-700' : 'bg-slate-100 text-slate-500',
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
            <div className="flex items-center gap-3 rounded-2xl bg-slate-50 px-3 py-3">
              <Avatar className="h-10 w-10 border-slate-200 bg-white">
                <AvatarFallback>AD</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-950">Ava Davis</p>
                <p className="truncate text-xs text-slate-500">HR Director</p>
              </div>
            </div>

            <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl px-3.5 text-slate-600 hover:bg-slate-100 hover:text-slate-900">
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      <div className="pl-[260px]">
        <header className="fixed left-[260px] right-0 top-0 z-20 border-b border-slate-200 bg-white">
          <div className="flex h-[60px] items-center justify-between gap-4 px-6">
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold text-slate-950">{pageTitle}</h1>
            </div>

            <div className="flex flex-1 items-center justify-end gap-3">
              <div className="relative w-full max-w-md">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input className="border-slate-200 bg-white pl-9" placeholder="Search employees, payroll, or leave requests" />
              </div>

              <Button variant="ghost" size="icon" className="rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-900" aria-label="Notifications">
                <Bell className="h-5 w-5" />
              </Button>

              <Avatar className="h-10 w-10 border-slate-200 bg-white">
                <AvatarFallback>AD</AvatarFallback>
              </Avatar>
            </div>
          </div>
        </header>

        <main className="h-screen overflow-y-auto bg-slate-50 pt-[60px]">
          <div className="min-h-full p-6">{children}</div>
        </main>
      </div>
    </div>
  )
}
