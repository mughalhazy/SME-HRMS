import type { ReactNode } from 'react'
import Link from 'next/link'
import { BriefcaseBusiness, CalendarDays, ClipboardList, LayoutGrid, Sparkles, TrendingUp, UserRoundSearch, Users, Wallet } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { navigationItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

const navIcons = {
  dashboard: LayoutGrid,
  employee_list: Users,
  employee_profile: UserRoundSearch,
  attendance_dashboard: CalendarDays,
  leave_requests: ClipboardList,
  payroll_dashboard: Wallet,
  job_postings: BriefcaseBusiness,
  candidate_pipeline: TrendingUp,
  performance_reviews: Sparkles,
}

function isPathActive(currentPath: string | undefined, href: string) {
  if (!currentPath) {
    return false
  }

  if (href === '/') {
    return currentPath === '/'
  }

  return currentPath === href || currentPath.startsWith(`${href}/`)
}

export function AppShell({ children, currentPath = '/' }: { children: ReactNode; currentPath?: string }) {
  const activeItem = navigationItems.find((item) => isPathActive(currentPath, item.href)) ?? navigationItems[0]

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white px-5 py-6 xl:border-b-0 xl:border-r xl:px-6 xl:py-8">
          <div className="space-y-6 xl:space-y-8">
            <div className="space-y-3">
              <Badge variant="success" className="w-fit">Enterprise UI</Badge>
              <Link href="/" className="flex items-center gap-3 text-slate-950">
                <span className="rounded-2xl bg-slate-950 p-3 text-white shadow-sm">
                  <BriefcaseBusiness className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-lg font-semibold tracking-tight">SME HRMS</p>
                  <p className="text-sm text-slate-500">Canonical frontend workspace</p>
                </div>
              </Link>
              <p className="text-sm leading-6 text-slate-600">
                All nine documented UI surfaces are exposed here with canonical read-model mapping and clean responsive navigation.
              </p>
            </div>

            <nav aria-label="Primary navigation" className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
              {navigationItems.map((item) => {
                const Icon = navIcons[item.key]
                const active = isPathActive(currentPath, item.href)

                return (
                  <Link
                    key={item.key}
                    href={item.href}
                    className={cn(
                      'flex items-start gap-3 rounded-2xl border px-4 py-3 transition-colors',
                      active
                        ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-100',
                    )}
                  >
                    <span className={cn('mt-0.5 rounded-xl p-2', active ? 'bg-white/10 text-white' : 'bg-slate-100 text-slate-700')}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="min-w-0 space-y-1">
                      <span className="block text-sm font-semibold">{item.label}</span>
                      <span className={cn('block text-xs leading-5', active ? 'text-slate-200' : 'text-slate-500')}>
                        {item.description}
                      </span>
                    </span>
                  </Link>
                )
              })}
            </nav>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
            <div className="flex flex-col gap-4 px-5 py-4 sm:px-6 lg:px-8">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-slate-500">Frontend quality control workspace</p>
                  <h1 className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">{activeItem.label}</h1>
                  <p className="max-w-3xl text-sm leading-6 text-slate-600">{activeItem.description}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {activeItem.readModels.map((model) => (
                    <Badge key={model} variant="outline">{model}</Badge>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap gap-2 overflow-x-auto pb-1">
                {navigationItems.map((item) => (
                  <Link
                    key={`${item.key}-chip`}
                    href={item.href}
                    className={cn(
                      'inline-flex whitespace-nowrap rounded-full border px-3 py-1.5 text-sm font-medium transition-colors',
                      isPathActive(currentPath, item.href)
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-950',
                    )}
                  >
                    {item.shortLabel}
                  </Link>
                ))}
              </div>
            </div>
          </header>

          <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-5 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  )
}
