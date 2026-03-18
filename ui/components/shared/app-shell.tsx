'use client'

import type { MouseEvent, ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { BriefcaseBusiness, CalendarDays, ClipboardList, LayoutGrid, LoaderCircle, Sparkles, TrendingUp, UserRoundSearch, Users, Wallet } from 'lucide-react'

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

function shouldHandleNavigation(event: MouseEvent<HTMLAnchorElement>, href: string, pathname: string) {
  if (event.defaultPrevented) {
    return false
  }

  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return false
  }

  if (!href.startsWith('/')) {
    return false
  }

  return href !== pathname
}

export function AppShell({ children, currentPath = '/' }: { children: ReactNode; currentPath?: string }) {
  const routePathname = usePathname() ?? currentPath
  const activePath = currentPath || routePathname
  const [pendingHref, setPendingHref] = useState<string | null>(null)

  useEffect(() => {
    setPendingHref(null)
  }, [routePathname])

  const activeItem = useMemo(() => navigationItems.find((item) => isPathActive(activePath, item.href)) ?? navigationItems[0], [activePath])

  const onNavigationStart = (href: string) => (event: MouseEvent<HTMLAnchorElement>) => {
    if (!shouldHandleNavigation(event, href, routePathname)) {
      return
    }

    setPendingHref(href)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <div
        aria-hidden="true"
        className={cn(
          'fixed inset-x-0 top-0 z-[70] h-1 origin-left bg-slate-950/85 transition-transform duration-200 ease-out',
          pendingHref ? 'scale-x-100' : 'scale-x-0',
        )}
      />

      <div className="mx-auto grid min-h-screen max-w-screen-2xl grid-cols-1 xl:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white px-5 py-5 xl:border-b-0 xl:border-r xl:px-5 xl:py-6">
          <div className="space-y-6">
            <div className="space-y-2.5">
              <Badge variant="success" className="w-fit">Enterprise UI</Badge>
              <Link href="/" onClick={onNavigationStart('/')} className="group flex items-center gap-3 text-slate-950 transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99]">
                <span className="rounded-xl bg-slate-950 p-2.5 text-white shadow-sm transition-transform duration-150 group-hover:scale-[1.02] group-active:scale-[0.98]">
                  <BriefcaseBusiness className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-base font-semibold tracking-tight">SME HRMS</p>
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
                const active = isPathActive(activePath, item.href)
                const isPending = pendingHref === item.href

                return (
                  <Link
                    key={item.key}
                    href={item.href}
                    onClick={onNavigationStart(item.href)}
                    aria-busy={isPending}
                    className={cn(
                      'flex items-start gap-3 rounded-xl border px-3.5 py-3 transition-[background-color,border-color,color,box-shadow,transform,opacity] duration-150 ease-out hover:-translate-y-px active:translate-y-0 active:scale-[0.99]',
                      active
                        ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-100',
                      isPending && 'opacity-85',
                    )}
                  >
                    <span className={cn('mt-0.5 rounded-xl p-2 transition-transform duration-150', active ? 'bg-white/10 text-white' : 'bg-slate-100 text-slate-700')}>
                      {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
                    </span>
                    <span className="min-w-0 space-y-1">
                      <span className="block text-sm font-semibold">{item.label}</span>
                      <span className={cn('block text-xs leading-5', active ? 'text-slate-200' : 'text-slate-500')}>
                        {isPending ? 'Opening…' : item.description}
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
            <div className="flex flex-col gap-3 px-4 py-3 sm:px-6 lg:px-7">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Frontend quality control workspace</p>
                    {pendingHref ? (
                      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                        <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                        Navigating…
                      </span>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h1 className="text-lg font-semibold tracking-tight text-slate-950">{activeItem.label}</h1>
                    <p className="text-sm text-slate-600">{activeItem.description}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {activeItem.readModels.map((model) => (
                    <Badge key={model} variant="outline">{model}</Badge>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5 overflow-x-auto pb-0.5">
                {navigationItems.map((item) => {
                  const active = isPathActive(activePath, item.href)
                  const isPending = pendingHref === item.href

                  return (
                    <Link
                      key={`${item.key}-chip`}
                      href={item.href}
                      onClick={onNavigationStart(item.href)}
                      aria-busy={isPending}
                      className={cn(
                        'inline-flex whitespace-nowrap rounded-full border px-3 py-1 text-sm font-medium transition-[background-color,border-color,color,transform,opacity] duration-150 ease-out hover:-translate-y-px active:translate-y-0 active:scale-[0.98]',
                        active
                          ? 'border-slate-900 bg-slate-900 text-white'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-950',
                        isPending && 'opacity-85',
                      )}
                    >
                      {item.shortLabel}
                    </Link>
                  )
                })}
              </div>
            </div>
          </header>

          <main key={routePathname} className="mx-auto flex w-full max-w-7xl flex-1 animate-[page-enter_180ms_ease-out] flex-col gap-6 px-6 py-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
