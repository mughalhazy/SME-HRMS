'use client'

import type { MouseEvent, ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import {
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ClipboardList,
  LayoutGrid,
  LoaderCircle,
  ShieldCheck,
  TrendingUp,
  UserRoundSearch,
  Users,
  Wallet,
} from 'lucide-react'

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
    <div className="min-h-screen bg-white text-black">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[16rem_minmax(0,1fr)]">
        <aside className="w-64 border-b border-gray-200 bg-white lg:border-b-0 lg:border-r">
          <div className="flex h-full flex-col gap-6 p-6">
            <div className="space-y-1">
              <Link href="/" onClick={onNavigationStart('/')} className="inline-flex items-center text-base font-semibold text-black">
                SME HRMS
              </Link>
              <p className="text-sm text-gray-500">Enterprise workspace</p>
            </div>

            <nav aria-label="Primary navigation" className="space-y-6">
              {groupedNavigation.map((section) => (
                <div key={section.key} className="space-y-2">
                  <p className="px-3 text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">{section.title}</p>
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
                            'flex items-center gap-3 px-3 py-2 rounded-md text-sm text-gray-600 transition-colors',
                            'hover:bg-gray-100 hover:text-black',
                            active && 'bg-gray-200 text-black',
                          )}
                        >
                          {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
                          <span>{item.label}</span>
                        </Link>
                      )
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col bg-white">
          <header className="border-b border-gray-200 bg-white">
            <div className="flex min-h-16 items-center justify-between gap-4 p-6">
              <div className="min-w-0">
                <h1 className="truncate text-xl font-semibold text-black">{activeItem.label}</h1>
                {pendingHref ? <p className="mt-1 text-sm text-gray-500">Opening {navigationItems.find((item) => item.href === pendingHref)?.label ?? 'page'}…</p> : null}
              </div>
              {pageActions ? <div className="flex shrink-0 items-center gap-3">{pageActions}</div> : <div />}
            </div>
          </header>

          <main className="flex-1 p-6">{children}</main>
        </div>
      </div>
    </div>
  )
}
