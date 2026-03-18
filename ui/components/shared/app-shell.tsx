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

const navigationSections = [
  {
    title: 'Overview',
    items: ['dashboard'],
  },
  {
    title: 'People',
    items: ['employee_list', 'employee_profile'],
  },
  {
    title: 'Operations',
    items: ['attendance_dashboard', 'leave_requests', 'payroll_dashboard'],
  },
  {
    title: 'Talent',
    items: ['job_postings', 'candidate_pipeline', 'performance_reviews'],
  },
] as const

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

  const groupedNavigation = useMemo(
    () =>
      navigationSections
        .map((section) => ({
          title: section.title,
          items: section.items
            .map((key) => navigationItems.find((item) => item.key === key))
            .filter((item): item is (typeof navigationItems)[number] => Boolean(item)),
        }))
        .filter((section) => section.items.length > 0),
    [],
  )

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

      <div className="mx-auto grid min-h-screen max-w-screen-2xl grid-cols-1 xl:grid-cols-[252px_minmax(0,1fr)]">
        <aside className="border-b border-gray-200 bg-white px-4 py-5 xl:border-b-0 xl:border-r xl:px-4 xl:py-6">
          <div className="space-y-6">
            <div className="space-y-3">
              <Badge variant="success" className="w-fit">Enterprise UI</Badge>
              <Link href="/" onClick={onNavigationStart('/')} className="group flex items-center gap-3 text-slate-950 transition-colors duration-150 hover:text-black">
                <span className="rounded-lg border border-gray-200 bg-gray-50 p-2 text-slate-700 transition-colors duration-150 group-hover:bg-gray-100 group-hover:text-slate-900">
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

            <nav aria-label="Primary navigation" className="space-y-1">
              {groupedNavigation.map((section, sectionIndex) => (
                <div key={section.title} className={cn(sectionIndex > 0 && 'mt-6')}>
                  <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">{section.title}</p>
                  <div className="space-y-1">
                    {section.items.map((item) => {
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
                            'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-[background-color,color,opacity] duration-150 ease-out',
                            active ? 'bg-gray-200 font-semibold text-black' : 'font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900',
                            isPending && 'opacity-85',
                          )}
                        >
                          <span
                            className={cn(
                              'flex h-4 w-4 shrink-0 items-center justify-center',
                              active ? 'text-gray-900' : 'text-gray-500',
                            )}
                          >
                            {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
                          </span>
                          <span className="min-w-0 flex-1 truncate">{item.label}</span>
                        </Link>
                      )
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="sticky top-0 z-30 border-b border-slate-200 bg-white backdrop-blur">
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

            </div>
          </header>

          <div className="border-b border-gray-200 bg-white px-6 lg:px-7">
            <div className="mx-auto flex w-full max-w-7xl overflow-x-auto">
              <nav aria-label="Secondary navigation" className="flex min-w-max items-center gap-6">
                {navigationItems.map((item) => {
                  const active = isPathActive(activePath, item.href)
                  const isPending = pendingHref === item.href

                  return (
                    <Link
                      key={`${item.key}-tab`}
                      href={item.href}
                      onClick={onNavigationStart(item.href)}
                      aria-busy={isPending}
                      className={cn(
                        'inline-flex whitespace-nowrap border-b-2 border-transparent px-4 py-2 text-sm text-gray-600 transition-[border-color,color,opacity] duration-150 ease-out hover:bg-transparent hover:text-gray-900',
                        active && 'border-black text-black',
                        isPending && 'opacity-85',
                      )}
                    >
                      {item.shortLabel}
                    </Link>
                  )
                })}
              </nav>
            </div>
          </div>

          <main key={routePathname} className="flex-1 px-4 py-6 sm:px-6 lg:px-7">
            <div className="mx-auto flex w-full max-w-7xl animate-[page-enter_180ms_ease-out] flex-col">
              <div className="flex flex-1 flex-col gap-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                {children}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
