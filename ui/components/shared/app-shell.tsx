'use client'

import type { MouseEvent, ReactNode } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Bell, ChevronDown, LoaderCircle, Search, Settings2 } from 'lucide-react'

import { useAuth } from '@/components/auth/auth-provider'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { getNavigationItem, isNavigationItemActive, navigationSections, primaryNavigationItems, utilityNavigationItems } from '@/lib/navigation'
import { cn } from '@/lib/utils'

const NAV_ITEM_GAP = 24
const NAV_ROOT_GAP = 16

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

function getVisibleNavigationCount(itemWidths: number[], availableWidth: number, moreWidth: number) {
  let visibleCount = itemWidths.length

  for (let count = itemWidths.length; count >= 0; count -= 1) {
    const hiddenCount = itemWidths.length - count
    const visibleWidth = itemWidths.slice(0, count).reduce((total, width) => total + width, 0)
    const visibleGapWidth = count > 1 ? (count - 1) * NAV_ITEM_GAP : 0
    const moreGapWidth = hiddenCount > 0 && count > 0 ? NAV_ITEM_GAP : 0
    const totalWidth = visibleWidth + visibleGapWidth + (hiddenCount > 0 ? moreGapWidth + moreWidth : 0)

    if (totalWidth <= availableWidth) {
      visibleCount = count
      break
    }
  }

  return visibleCount
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
  const router = useRouter()
  const pathname = usePathname() ?? currentPath ?? '/dashboard'
  const activePath = currentPath ?? pathname
  const { session } = useAuth()
  const [pendingHref, setPendingHref] = useState<string | null>(null)
  const [visibleNavigationCount, setVisibleNavigationCount] = useState(primaryNavigationItems.length)
  const navigationRootRef = useRef<HTMLDivElement | null>(null)
  const rightNavRef = useRef<HTMLDivElement | null>(null)
  const moreMeasureRef = useRef<HTMLButtonElement | null>(null)
  const itemMeasureRefs = useRef<Record<string, HTMLAnchorElement | null>>({})

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

  const recalculateNavigation = useCallback(() => {
    const navigationRoot = navigationRootRef.current
    const rightNav = rightNavRef.current
    const moreMeasure = moreMeasureRef.current

    if (!navigationRoot || !rightNav || !moreMeasure) {
      return
    }

    const itemWidths = primaryNavigationItems.map((item) => itemMeasureRefs.current[item.key]?.offsetWidth ?? 0)

    if (itemWidths.some((width) => width === 0)) {
      return
    }

    const availableWidth = Math.max(0, navigationRoot.clientWidth - rightNav.offsetWidth - NAV_ROOT_GAP)
    const nextVisibleCount = getVisibleNavigationCount(itemWidths, availableWidth, moreMeasure.offsetWidth)

    setVisibleNavigationCount((currentCount) => (currentCount === nextVisibleCount ? currentCount : nextVisibleCount))
  }, [])

  useLayoutEffect(() => {
    recalculateNavigation()

    const resizeObserver = new ResizeObserver(() => {
      recalculateNavigation()
    })

    if (navigationRootRef.current) {
      resizeObserver.observe(navigationRootRef.current)
    }

    if (rightNavRef.current) {
      resizeObserver.observe(rightNavRef.current)
    }

    Object.values(itemMeasureRefs.current).forEach((element) => {
      if (element) {
        resizeObserver.observe(element)
      }
    })

    if (moreMeasureRef.current) {
      resizeObserver.observe(moreMeasureRef.current)
    }

    window.addEventListener('resize', recalculateNavigation)

    return () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', recalculateNavigation)
    }
  }, [recalculateNavigation])

  const visibleNavigationItems = primaryNavigationItems.slice(0, visibleNavigationCount)
  const overflowNavigationItems = primaryNavigationItems.slice(visibleNavigationCount)
  const hasOverflowNavigation = overflowNavigationItems.length > 0
  const overflowActive = overflowNavigationItems.some((item) => isNavigationItemActive(activePath, item))

  const handleOverflowNavigation = (href: string) => {
    if (href === pathname) {
      return
    }

    setPendingHref(href)
    router.push(href)
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="grid min-h-20 grid-cols-12 items-center gap-x-6 gap-y-4 px-4 py-4 sm:px-6 xl:px-8">
          <div className="col-span-12 flex min-w-0 items-center lg:col-span-3 xl:col-span-2">
            <Link href="/dashboard" onClick={onNavigationStart('/dashboard')} className="flex min-w-0 items-center gap-3">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[var(--radius-control)] bg-[var(--primary)] text-sm font-semibold text-[var(--primary-foreground)]">
                HR
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold tracking-[0.18em] text-slate-500">Enterprise HRMS</span>
                <span className="block truncate text-lg font-semibold tracking-tight text-slate-950">SME HRMS</span>
              </span>
            </Link>
          </div>

          <div className="col-span-12 min-w-0 lg:col-span-9 xl:col-span-10">
            <div ref={navigationRootRef} className="flex w-full flex-wrap items-center justify-between gap-4">
              <nav aria-label="Primary navigation" className="flex min-w-0 flex-1 items-center gap-6 overflow-hidden">
                {visibleNavigationItems.map((item) => {
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
                        'inline-flex h-11 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-control)] border border-transparent px-4 text-sm font-semibold transition-[background-color,color,border-color,box-shadow] duration-150',
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

                {hasOverflowNavigation ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          'h-11 shrink-0 gap-2 whitespace-nowrap border-slate-200 bg-white px-4 text-sm font-semibold text-slate-600 shadow-none hover:bg-[var(--surface-subtle)] hover:text-slate-950',
                          overflowActive && 'border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--primary)]',
                        )}
                      >
                        <span>More</span>
                        <ChevronDown className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" className="w-56 p-1">
                      {overflowNavigationItems.map((item) => {
                        const active = isNavigationItemActive(activePath, item)
                        const isPending = pendingHref === item.href

                        return (
                          <button
                            key={item.key}
                            aria-current={active ? 'page' : undefined}
                            className={cn(
                              'flex w-full items-center justify-between gap-3 rounded-[calc(var(--radius-control)-4px)] px-3 py-2 text-left text-sm font-medium transition-colors hover:bg-[var(--accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]',
                              active ? 'bg-[var(--accent)] text-[var(--primary)]' : 'text-[var(--foreground)]',
                            )}
                            onClick={() => handleOverflowNavigation(item.href)}
                            role="menuitem"
                            type="button"
                          >
                            <span className="whitespace-nowrap">{item.label}</span>
                            {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
                          </button>
                        )
                      })}
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : null}
              </nav>

              <div ref={rightNavRef} className="flex shrink-0 items-center gap-3">
                <div className="flex shrink-0 items-center gap-3">
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

                <div className="flex min-w-0 shrink-0 items-center gap-3 rounded-[var(--radius-control)] border border-slate-200 bg-white px-3 py-2">
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
          </div>
        </div>

        <div aria-hidden="true" className="pointer-events-none absolute left-0 top-0 -z-10 opacity-0">
          <div className="flex items-center gap-6">
            {primaryNavigationItems.map((item) => (
              <Link
                key={item.key}
                href={item.href}
                ref={(element) => {
                  itemMeasureRefs.current[item.key] = element
                }}
                className="inline-flex h-11 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-control)] border border-transparent px-4 text-sm font-semibold"
                tabIndex={-1}
              >
                <span>{item.label}</span>
              </Link>
            ))}
            <Button
              ref={moreMeasureRef}
              variant="outline"
              className="h-11 shrink-0 gap-2 whitespace-nowrap border-slate-200 bg-white px-4 text-sm font-semibold text-slate-600 shadow-none"
              tabIndex={-1}
            >
              <span>More</span>
              <ChevronDown className="h-4 w-4" />
            </Button>
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
