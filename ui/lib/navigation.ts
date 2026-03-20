export type NavigationSectionKey = 'overview' | 'workforce' | 'operations' | 'talent' | 'admin'

export type NavigationItemKey =
  | 'dashboard'
  | 'employees'
  | 'attendance'
  | 'leave'
  | 'payroll'
  | 'hiring'
  | 'performance'
  | 'organization'
  | 'settings'
  | 'notifications'

export type NavigationItem = {
  key: NavigationItemKey
  href: string
  label: string
  shortLabel: string
  icon: 'layout' | 'users' | 'clock' | 'calendar' | 'wallet' | 'briefcase' | 'chart' | 'building' | 'settings' | 'bell'
  description: string
  section: NavigationSectionKey
  matcherPrefixes: string[]
}

export const navigationSections: { key: NavigationSectionKey; title: string }[] = [
  { key: 'overview', title: 'Overview' },
  { key: 'workforce', title: 'Workforce' },
  { key: 'operations', title: 'Operations' },
  { key: 'talent', title: 'Talent' },
  { key: 'admin', title: 'Admin' },
]

export const navigationItems: NavigationItem[] = [
  {
    key: 'dashboard',
    href: '/dashboard',
    label: 'Dashboard',
    shortLabel: 'Dashboard',
    icon: 'layout',
    description: 'Track workforce health, approvals, and operational priorities from one calm command center.',
    section: 'overview',
    matcherPrefixes: ['/dashboard'],
  },
  {
    key: 'employees',
    href: '/employees',
    label: 'Employees',
    shortLabel: 'Employees',
    icon: 'users',
    description: 'Manage employee records, search the directory, and move into detailed profiles without losing context.',
    section: 'workforce',
    matcherPrefixes: ['/employees'],
  },
  {
    key: 'organization',
    href: '/organization',
    label: 'Organization',
    shortLabel: 'Organization',
    icon: 'building',
    description: 'Review departments, role coverage, and staffing structure with clean organizational visibility.',
    section: 'workforce',
    matcherPrefixes: ['/organization', '/departments', '/roles'],
  },
  {
    key: 'attendance',
    href: '/attendance',
    label: 'Attendance',
    shortLabel: 'Attendance',
    icon: 'clock',
    description: 'Monitor daily presence, identify exceptions, and keep time-tracking workflows aligned.',
    section: 'operations',
    matcherPrefixes: ['/attendance'],
  },
  {
    key: 'leave',
    href: '/leave',
    label: 'Leave',
    shortLabel: 'Leave',
    icon: 'calendar',
    description: 'Review leave requests, balances, and team coverage with consistent filters and approvals.',
    section: 'operations',
    matcherPrefixes: ['/leave', '/leave-requests'],
  },
  {
    key: 'payroll',
    href: '/payroll',
    label: 'Payroll',
    shortLabel: 'Payroll',
    icon: 'wallet',
    description: 'Track payroll cycles, exceptions, and settlement readiness across the organization.',
    section: 'operations',
    matcherPrefixes: ['/payroll'],
  },
  {
    key: 'hiring',
    href: '/hiring',
    label: 'Hiring',
    shortLabel: 'Hiring',
    icon: 'briefcase',
    description: 'Keep requisitions and candidate flow in one polished hiring workspace.',
    section: 'talent',
    matcherPrefixes: ['/hiring', '/job-postings', '/candidate-pipeline'],
  },
  {
    key: 'performance',
    href: '/performance',
    label: 'Performance',
    shortLabel: 'Performance',
    icon: 'chart',
    description: 'Review cycle progress, calibration status, and manager follow-up across the business.',
    section: 'talent',
    matcherPrefixes: ['/performance', '/performance-reviews'],
  },
  {
    key: 'settings',
    href: '/settings',
    label: 'Settings',
    shortLabel: 'Settings',
    icon: 'settings',
    description: 'Configure company-wide HR defaults, integrations, and operational controls.',
    section: 'admin',
    matcherPrefixes: ['/settings'],
  },
  {
    key: 'notifications',
    href: '/notifications',
    label: 'Notifications',
    shortLabel: 'Inbox',
    icon: 'bell',
    description: 'Review event-driven inbox items, delivery outcomes, and suppressed channels in one place.',
    section: 'admin',
    matcherPrefixes: ['/notifications'],
  },
]

export const primaryNavigationItems = navigationItems.filter((item) =>
  ['dashboard', 'employees', 'organization', 'attendance', 'leave', 'payroll', 'hiring', 'performance'].includes(item.key),
)

export const utilityNavigationItems = navigationItems.filter((item) => ['notifications', 'settings'].includes(item.key))

export function isNavigationItemActive(pathname: string | undefined, item: NavigationItem) {
  if (!pathname) {
    return false
  }

  return item.matcherPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))
}

export function getNavigationItem(pathname: string | undefined) {
  return navigationItems.find((item) => isNavigationItemActive(pathname, item)) ?? navigationItems[0]
}
