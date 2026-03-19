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
  Settings2,
  Sparkles,
  Target,
  Users,
  Wallet,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getNavigationItem, isNavigationItemActive, navigationSections, sidebarNavigationItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

const navIcons = {
  layout: LayoutGrid,
  users: Users,
  clock: CalendarDays,
  calendar: ClipboardList,
  wallet: Wallet,
  briefcase: BriefcaseBusiness,
  chart: Target,
  building: Building2,
  settings: Settings2,
  bell: Bell,
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
  currentPath,
  pageTitle,
  pageDescription,
  pageActions,
}: {
  children: ReactNode
  currentPath?: string
  pageTitle?: string
  pageDescription?: string
  pageActions?: ReactNode
}) {
  const pathname = usePathname() ?? currentPath ?? '/dashboard'
  const activePath = currentPath ?? pathname
  const [pendingHref, setPendingHref] = useState<string | null>(null)

  useEffect(() => {
    setPendingHref(null)
  }, [pathname])

  const activeItem = useMemo(() => getNavigationItem(activePath), [activePath])

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
    if (!shouldHandleNavigation(event, href, pathname)) {
      return
    }

    setPendingHref(href)
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.09),_transparent_28%),linear-gradient(180deg,#f8fafc_0%,#f8fafc_45%,#eef2ff_100%)] text-slate-950">
      <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[19rem_minmax(0,1fr)]">
        <aside className="border-b border-slate-200/80 bg-white/90 backdrop-blur xl:border-b-0 xl:border-r">
          <div className="sticky top-0 flex h-full max-h-screen flex-col gap-6 overflow-y-auto p-6">
            <div className="space-y-3">
              <Badge className="w-fit bg-slate-950 text-white hover:bg-slate-950">Enterprise HRMS</Badge>
              <div className="space-y-2">
                <Link href="/dashboard" onClick={onNavigationStart('/dashboard')} className="inline-flex items-center gap-2 text-lg font-semibold tracking-tight text-slate-950">
                  <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-600 text-sm font-semibold text-white shadow-lg shadow-blue-200">HR</span>
                  <span>SME HRMS</span>
                </Link>
                <p className="text-sm leading-6 text-slate-500">People, payroll, attendance, hiring, and performance operations in one refined workspace.</p>
              </div>
            </div>

            <nav aria-label="Primary navigation" className="space-y-6">
              {groupedNavigation.map((section) => (
                <div key={section.key} className="space-y-2.5">
                  <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">{section.title}</p>
                  <div className="space-y-1.5">
                    {section.items.map((item) => {
                      const Icon = navIcons[item.icon]
                      const active = isNavigationItemActive(activePath, item)
                      const isPending = pendingHref === item.href

                      return (
                        <Link
                          key={item.key}
                          href={item.href}
                          onClick={onNavigationStart(item.href)}
                          aria-busy={isPending}
                          className={cn(
                            'group flex items-start gap-3 rounded-2xl border px-3.5 py-3 text-sm transition-all',
                            active
                              ? 'border-blue-100 bg-gradient-to-br from-blue-50 via-indigo-50 to-white text-slate-950 shadow-sm'
                              : 'border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-950',
                          )}
                        >
                          <span
                            className={cn(
                              'mt-0.5 rounded-xl p-2.5 transition-colors',
                              active ? 'bg-white text-blue-700 shadow-sm ring-1 ring-blue-100' : 'bg-slate-100 text-slate-500 group-hover:bg-white',
                            )}
                          >
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

            <div className="mt-auto rounded-3xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-white p-3 text-blue-700 shadow-sm ring-1 ring-slate-200">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div className="space-y-1.5">
                  <p className="text-sm font-semibold text-slate-950">Workspace quality pass</p>
                  <p className="text-xs leading-5 text-slate-500">Consistent route flow, nested active states, and polished module navigation are now enforced from one config.</p>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 backdrop-blur-xl">
            <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 xl:flex-row xl:items-center xl:justify-between">
              <div className="min-w-0 space-y-1.5">
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="truncate text-2xl font-semibold tracking-tight text-slate-950">{pageTitle ?? activeItem.label}</h1>
                  <Badge variant="outline" className="border-blue-100 bg-blue-50 text-blue-700">
                    {navigationSections.find((section) => section.key === activeItem.section)?.title ?? 'Workspace'}
                  </Badge>
                  <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-600">Live workspace</Badge>
                </div>
                <p className="max-w-3xl text-sm leading-6 text-slate-500">
                  {pendingHref ? `Opening ${sidebarNavigationItems.find((item) => item.href === pendingHref)?.label ?? 'page'}…` : pageDescription ?? activeItem.description}
                </p>
              </div>

              <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
                <div className="relative min-w-[280px]">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input className="h-11 rounded-xl border-slate-200 bg-white pl-9 shadow-sm" placeholder="Search employees, payroll, reviews, or policies" />
                </div>
                <div className="flex items-center gap-3">
                  <Link href="/notifications" onClick={onNavigationStart('/notifications')}>
                    <Button variant="outline" size="icon" className="h-11 w-11 rounded-xl border-slate-200 bg-white shadow-sm hover:bg-slate-50" aria-label="Notifications">
                      <Bell className="h-4 w-4" />
                    </Button>
                  </Link>
                  {pageActions ?? (
                    <>
                      <Button variant="outline" className="h-11 rounded-xl border-slate-200 bg-white shadow-sm hover:bg-slate-50">Export</Button>
                      <Button className="h-11 rounded-xl shadow-sm">New request</Button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1">
            <div className="mx-auto w-full max-w-7xl p-4 sm:p-6">{children}</div>
          </main>
        </div>
      </div>
    </div>
  )
}
