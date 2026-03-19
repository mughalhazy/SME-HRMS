import { Bell, Building2, CalendarDays, ClipboardList, LayoutGrid, Search, Settings2, Users, Wallet, BriefcaseBusiness, TrendingUp } from 'lucide-react'
import type { ReactNode } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { navigationItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

const navIcons = {
  dashboard: LayoutGrid,
  employees: Users,
  departments: Building2,
  roles: Bell,
  employee_profile: Building2,
  attendance: CalendarDays,
  leave: ClipboardList,
  payroll: Wallet,
  jobs: BriefcaseBusiness,
  candidates: TrendingUp,
  performance: Bell,
  settings: Settings2,
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--app-background)] text-[var(--foreground)]">
      <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-[var(--border)] bg-[var(--sidebar-background)] px-6 py-8 lg:border-b-0 lg:border-r">
          <div className="space-y-8">
            <div className="space-y-3">
              <Badge className="w-fit" variant="success">Enterprise UI</Badge>
              <div className="space-y-1">
                <h1 className="text-xl font-semibold tracking-tight">SME HRMS</h1>
                <p className="text-sm leading-6 text-[var(--muted-foreground)]">
                  Canonical navigation and reusable interface primitives for HR operations.
                </p>
              </div>
            </div>

            <nav className="space-y-2" aria-label="Primary navigation">
              {navigationItems.map((item, index) => {
                const Icon = navIcons[item.key]
                const active = index === 0

                return (
                  <a
                    key={item.key}
                    className={cn(
                      'flex items-start gap-3 rounded-xl border px-4 py-3 transition-colors',
                      active
                        ? 'border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--foreground)]'
                        : 'border-transparent text-[var(--muted-foreground)] hover:border-[var(--border)] hover:bg-[var(--surface)] hover:text-[var(--foreground)]',
                    )}
                    href={`#surface-${item.key}`}
                  >
                    <span className={cn('mt-0.5 rounded-lg p-2', active ? 'bg-[var(--surface)] text-[var(--primary)]' : 'bg-[var(--surface)]')}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="min-w-0 space-y-1">
                      <span className="block text-sm font-medium">{item.label}</span>
                      <span className="block text-xs leading-5 text-[var(--muted-foreground)]">{item.description}</span>
                    </span>
                  </a>
                )
              })}
            </nav>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="sticky top-0 z-20 border-b border-[var(--border)] bg-[var(--surface)] backdrop-blur">
            <div className="flex flex-col gap-4 px-6 py-4 md:flex-row md:items-center md:justify-between lg:px-8">
              <div className="space-y-1">
                <p className="text-sm font-medium text-[var(--muted-foreground)]">Frontend UI system</p>
                <h2 className="text-2xl font-semibold tracking-tight">Operational workspace foundation</h2>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative min-w-[260px] flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
                  <Input className="pl-9" placeholder="Search people, payroll, or reviews" />
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline">{navigationItems.length} surfaces</Badge>
                  <Button variant="outline">Open command menu</Button>
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 px-6 py-8 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  )
}
