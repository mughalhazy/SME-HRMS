import type { ReactNode } from 'react'
import Link from 'next/link'
import { BriefcaseBusiness, PlusCircle, Users } from 'lucide-react'

import { cn } from '@/lib/utils'

const navItems = [
  { href: '/employees', label: 'Employees', icon: Users },
  { href: '/employees/new', label: 'Add employee', icon: PlusCircle },
]

export function AppShell({ children, currentPath }: { children: ReactNode; currentPath?: string }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-4">
          <Link href="/employees" className="flex items-center gap-3 font-semibold tracking-tight text-slate-900">
            <span className="rounded-xl bg-slate-900 p-2 text-white">
              <BriefcaseBusiness className="h-5 w-5" />
            </span>
            <span>
              SME HRMS
              <span className="ml-2 text-sm font-medium text-slate-500">Employee module</span>
            </span>
          </Link>
          <nav className="flex flex-wrap items-center gap-2">
            {navItems.map(({ href, label, icon: Icon }) => {
              const active = currentPath === href
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    'inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors',
                    active ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200',
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              )
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">{children}</main>
    </div>
  )
}
