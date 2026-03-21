'use client'

import type { MouseEvent, ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { Bell, LoaderCircle, Search, Settings2 } from 'lucide-react'

import { useAuth } from '@/components/auth/auth-provider'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getNavigationItem, isNavigationItemActive, navigationSections, primaryNavigationItems, utilityNavigationItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

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

function formatProfileLabel(role: string | undefined) {
  if (!role) {
    return 'HR workspace'
  }

  return role
    .split('_')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1).toLowerCase())
    .join(' ')
}

function getProfileInitials(identifier: string | null | undefined) {
  if (!identifier) {
    return 'HR'
  }

  return identifier
    .split(/[^a-zA-Z0-9]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((segment) => segment.charAt(0).toUpperCase())
    .join('')
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
  const { session } = useAuth()
  const [pendingHref, setPendingHref] = useState<string | null>(null)

  useEffect(() => {
    setPendingHref(null)
  }, [pathname])

  const activeItem = useMemo(() => getNavigationItem(activePath), [activePath])
  const activeSection = navigationSections.find((section) => section.key === activeItem.section)?.title ?? 'Workspace'
  const profileName = session?.user.user_id ?? 'workspace.user'
  const profileRole = formatProfileLabel(session?.user.role)

  const onNavigationStart = (href: string) => (event: MouseEvent<HTMLAnchorElement>) => {
    if (!shouldHandleNavigation(event, href, pathname)) {
      return
    }

    setPendingHref(href)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="grid min-h-20 grid-cols-12 items-center gap-x-6 gap-y-4 px-4 py-4 sm:px-6 xl:px-8">
          <div className="col-span-12 flex min-w-0 items-center lg:col-span-3 xl:col-span-2">
            <Link href="/dashboard" onClick={onNavigationStart('/dashboard')} className="flex min-w-0 items-center gap-3">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--primary)] text-sm font-semibold text-[var(--primary-foreground)]">
                HR
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold tracking-[0.18em] text-slate-500">Enterprise HRMS</span>
                <span className="block truncate text-lg font-semibold tracking-tight text-slate-950">SME HRMS</span>
              </span>
            </Link>
          </div>

          <div className="col-span-12 min-w-0 lg:col-span-6 xl:col-span-7">
            <nav
              aria-label="Primary navigation"
              className="overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            >
              <div className="flex min-w-max items-center gap-1.5 lg:justify-center">
                {primaryNavigationItems.map((item) => {
                  const active = isNavigationItemActive(activePath, item)
                  const isPending = pendingHref === item.href

                  return (
                    <Link
                      key={item.key}
                      href={item.href}
                      onClick={onNavigationStart(item.href)}
                      aria-current={active ? 'page' : undefined}
                      aria-busy={isPending}
                      className={cn(
                        'inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] border border-transparent px-4 text-sm font-semibold whitespace-nowrap transition-[background-color,color,border-color,box-shadow] duration-150',
                        active
                          ? 'border-[var(--border)] bg-[var(--surface)] text-[var(--primary)] shadow-[var(--shadow-control)]'
                          : 'text-slate-600 hover:bg-[var(--surface-subtle)] hover:text-slate-950',
                      )}
                    >
                      {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>
            </nav>
          </div>

          <div className="col-span-12 flex min-w-0 items-center justify-between gap-3 lg:col-span-3 lg:justify-end xl:col-span-3">
            <div className="flex items-center gap-2">
              {utilityNavigationItems.map((item) => {
                const Icon = item.icon === 'bell' ? Bell : Settings2
                const active = isNavigationItemActive(activePath, item)
                const isPending = pendingHref === item.href

                return (
                  <Link key={item.key} href={item.href} onClick={onNavigationStart(item.href)} aria-label={item.label} aria-current={active ? 'page' : undefined}>
                    <Button
                      variant="outline"
                      size="icon"
                      className={cn(
                        'h-10 w-10 rounded-[var(--radius-control)] border-slate-200 bg-white text-slate-600 shadow-none transition-[background-color,color,border-color] duration-150 hover:bg-[var(--surface-subtle)] hover:text-slate-950',
                        active && 'border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--primary)]',
                      )}
                    >
                      {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}
                    </Button>
                  </Link>
                )
              })}
            </div>

            <div className="flex min-w-0 items-center gap-3 rounded-[var(--radius-surface)] border border-slate-200 bg-white px-3 py-2">
              <Avatar className="h-10 w-10 border-slate-200">
                <AvatarFallback>{getProfileInitials(profileName)}</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-950">{profileName}</p>
                <p className="truncate text-xs text-slate-500">{profileRole}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="px-4 pb-6 pt-6 sm:px-6 xl:px-8">
        <section className="grid grid-cols-12 gap-6">
          <div className="col-span-12 min-w-0 space-y-6">
            <div className="grid grid-cols-12 gap-4 border-b border-slate-200 pb-6 xl:gap-6">
              <div className="col-span-12 min-w-0 space-y-2 xl:col-span-7">
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="truncate text-2xl font-semibold tracking-tight text-slate-950">{pageTitle ?? activeItem.label}</h1>
                  <Badge variant="outline" className="border-slate-200 bg-slate-100 text-slate-700">
                    {activeSection}
                  </Badge>
                </div>
                <p className="max-w-4xl text-sm leading-6 text-slate-600">
                  {pendingHref ? `Opening ${primaryNavigationItems.find((item) => item.href === pendingHref)?.label ?? 'page'}…` : pageDescription ?? activeItem.description}
                </p>
              </div>

              <div className="col-span-12 flex flex-col gap-3 xl:col-span-5 xl:items-end xl:justify-end">
                <div className="relative w-full xl:max-w-[360px]">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input className="h-11 border-slate-200 bg-white pl-9 shadow-none" placeholder="Search employees, payroll, reviews, or policies" />
                </div>
                <div className="flex w-full flex-wrap items-center gap-3 xl:w-auto xl:justify-end">{pageActions ?? <Button className="h-11 shadow-none">New request</Button>}</div>
              </div>
            </div>

            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-12 min-w-0">{children}</div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
