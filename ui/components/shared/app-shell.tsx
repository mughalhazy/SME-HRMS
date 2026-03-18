'use client'

import type { MouseEvent, ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { BriefcaseBusiness, CalendarDays, ClipboardList, LayoutGrid, LoaderCircle, Sparkles, TrendingUp, UserRoundSearch, Users, Wallet } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { getReadModelLabel, navigationItems } from '@/lib/navigation'
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
    key: 'overview',
    title: 'Overview',
    secondaryLabel: 'Dashboard context',
    items: ['dashboard'],
  },
  {
    key: 'people',
    title: 'People',
    secondaryLabel: 'People workflows',
    items: ['employee_list', 'employee_profile'],
  },
  {
    key: 'operations',
    title: 'Operations',
    secondaryLabel: 'Operations workflows',
    items: ['attendance_dashboard', 'leave_requests', 'payroll_dashboard'],
  },
  {
    key: 'talent',
    title: 'Talent',
    secondaryLabel: 'Talent workflows',
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
          ...section,
          items: section.items
            .map((key) => navigationItems.find((item) => item.key === key))
            .filter((item): item is (typeof navigationItems)[number] => Boolean(item)),
        }))
        .filter((section) => section.items.length > 0),
    [],
  )

  const activeSection = useMemo(
    () => groupedNavigation.find((section) => section.items.some((item) => isPathActive(activePath, item.href))) ?? groupedNavigation[0],
    [activePath, groupedNavigation],
  )

  const onNavigationStart = (href: string) => (event: MouseEvent<HTMLAnchorElement>) => {
    if (!shouldHandleNavigation(event, href, routePathname)) {
      return
    }

    setPendingHref(href)
  }

  return (
    <div className="min-h-screen bg-gray-50 text-slate-950">
      <div
        aria-hidden="true"
        className={cn(
          'fixed inset-x-0 top-0 z-[70] h-1 origin-left bg-slate-950/85 transition-transform duration-200 ease-out',
          pendingHref ? 'scale-x-100' : 'scale-x-0',
        )}
      />

      <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[252px_minmax(0,1fr)]">
        <aside className="border-b border-gray-200 bg-white px-4 py-5 xl:border-b-0 xl:border-r xl:px-4 xl:py-6">
          <div className="space-y-6">
            <div className="space-y-3 border-b border-gray-200 pb-6">
              <Badge variant="outline" className="w-fit border-gray-200 bg-white text-slate-700">Primary navigation</Badge>
              <Link href="/" onClick={onNavigationStart('/')} className="group flex items-center gap-3 text-slate-900 transition-colors duration-150 hover:text-slate-950">
                <span className="rounded-lg border border-gray-200 bg-gray-50 p-2 text-slate-700 transition-colors duration-150 group-hover:bg-gray-100">
                  <BriefcaseBusiness className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-base font-semibold tracking-tight">SME HRMS</p>
                  <p className="text-sm text-slate-500">Main application workspace</p>
                </div>
              </Link>
              <p className="text-sm leading-6 text-slate-600">
                Use the sidebar for primary movement across core HR domains. The top bar stays focused on the current section only.
              </p>
            </div>

            <nav aria-label="Primary navigation" className="space-y-1">
              {groupedNavigation.map((section, sectionIndex) => (
                <div key={section.key} className={cn(sectionIndex > 0 && 'mt-6')}>
                  <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{section.title}</p>
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
                            'flex items-start gap-3 rounded-lg border px-3 py-3 transition-[background-color,border-color,color,opacity] duration-150 ease-out',
                            active ? 'border-gray-200 bg-gray-50 text-slate-950' : 'border-transparent text-slate-600 hover:border-gray-200 hover:bg-white hover:text-slate-950',
                            isPending && 'opacity-85',
                          )}
                        >
                          <span
                            className={cn(
                              'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-gray-200',
                              active ? 'bg-white text-slate-900' : 'bg-gray-50 text-slate-500',
                            )}
                          >
                            {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block text-sm font-semibold text-inherit">{item.label}</span>
                            <span className="mt-1 block text-xs leading-5 text-slate-500">{item.description}</span>
                          </span>
                        </Link>
                      )
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col bg-gray-50">
          <header className="sticky top-0 z-30 border-b border-gray-200 bg-white">
            <div className="flex flex-col gap-3 px-4 py-3 sm:px-6 lg:px-7">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{activeSection?.secondaryLabel ?? 'Current workspace'}</p>
                    {pendingHref ? (
                      <span className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs font-medium text-slate-600">
                        <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                        Navigating…
                      </span>
                    ) : null}
                  </div>
                  <div className="flex flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-center sm:gap-2">
                    <h1 className="text-lg font-semibold tracking-tight text-slate-950">{activeItem.label}</h1>
                    <p className="text-sm text-slate-600">{activeItem.description}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {activeItem.readModels.map((model) => (
                    <Badge key={model} variant="outline" className="border-gray-200 bg-white text-slate-700">
                      {getReadModelLabel(model)}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 bg-gray-50 px-4 py-6 sm:px-6 lg:px-7">{children}</main>
        </div>
      </div>
    </div>
  )
}
