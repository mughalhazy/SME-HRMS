'use client'

import type { MouseEvent, ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import {
  Bell,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ClipboardList,
  LayoutGrid,
  LoaderCircle,
  Search,
  ShieldCheck,
  Settings2,
  TrendingUp,
  UserRoundSearch,
  Users,
  Wallet,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { navigationItems, navigationSections, sidebarNavigationItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

const navIcons = {
  dashboard: LayoutGrid,
  employees: Users,
  departments: Building2,
  roles: ShieldCheck,
  employee_profile: UserRoundSearch,
  attendance: CalendarDays,
  leave: ClipboardList,
  payroll: Wallet,
  jobs: BriefcaseBusiness,
  candidates: TrendingUp,
  performance: TrendingUp,
  settings: Settings2,
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

export function AppShell({
  children,
  currentPath = '/',
  pageActions,
}: {
  children: ReactNode
  currentPath?: string
  pageActions?: ReactNode
}) {
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
          items: sidebarNavigationItems.filter((item) => item.section === section.key),
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
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[17rem_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white lg:border-b-0 lg:border-r">
          <div className="flex h-full flex-col gap-6 p-6">
            <div className="space-y-3">
              <Badge className="w-fit">Enterprise HRMS</Badge>
              <div className="space-y-1">
                <Link href="/" onClick={onNavigationStart('/')} className="inline-flex items-center text-lg font-semibold tracking-tight text-slate-950">
                  SME HRMS
                </Link>
                <p className="text-sm leading-6 text-slate-500">People, payroll, and performance operations in one workspace.</p>
              </div>
            </div>

            <nav aria-label="Primary navigation" className="space-y-6">
              {groupedNavigation.map((section) => (
                <div key={section.key} className="space-y-2">
                  <p className="px-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{section.title}</p>
                  <div className="space-y-1.5">
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
                            'flex items-start gap-3 rounded-xl border px-3.5 py-3 text-sm transition-colors',
                            active
                              ? 'border-blue-100 bg-blue-50 text-slate-950'
                              : 'border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-950',
                          )}
                        >
                          <span className={cn('mt-0.5 rounded-lg p-2', active ? 'bg-white text-blue-700' : 'bg-slate-100 text-slate-500')}>
                            {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
                          </span>
                          <span className="min-w-0 space-y-1">
                            <span className="block font-medium">{item.label}</span>
                            <span className="block text-xs leading-5 text-slate-500">{item.description}</span>
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

        <div className="flex min-w-0 flex-col bg-slate-50">
          <header className="border-b border-slate-200 bg-white">
            <div className="flex flex-col gap-4 p-6 xl:flex-row xl:items-center xl:justify-between">
              <div className="min-w-0 space-y-1">
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="truncate text-2xl font-semibold tracking-tight text-slate-950">{activeItem.label}</h1>
                  <Badge variant="outline">Live workspace</Badge>
                </div>
                <p className="text-sm leading-6 text-slate-500">
                  {pendingHref ? `Opening ${navigationItems.find((item) => item.href === pendingHref)?.label ?? 'page'}…` : activeItem.description}
                </p>
              </div>

              <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
                <div className="relative min-w-[280px]">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input className="pl-9" placeholder="Search employees, payroll, or reviews" />
                </div>
                <div className="flex items-center gap-3">
                  <Button variant="outline" size="icon" aria-label="Notifications">
                    <Bell className="h-4 w-4" />
                  </Button>
                  {pageActions ?? (
                    <>
                      <Button variant="outline">Export</Button>
                      <Button>New request</Button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 p-6">{children}</main>
        </div>
      </div>
    </div>
  )
}
