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

export const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', path: '/dashboard' },
  { key: 'employees', label: 'Employees', path: '/employees' },
  { key: 'organization', label: 'Organization', path: '/organization' },
  { key: 'attendance', label: 'Attendance', path: '/attendance' },
  { key: 'leave', label: 'Leave', path: '/leave' },
  { key: 'payroll', label: 'Payroll', path: '/payroll' },
  { key: 'hiring', label: 'Hiring', path: '/hiring' },
  { key: 'performance', label: 'Performance', path: '/performance' },
] as const satisfies readonly {
  key: Exclude<NavigationItemKey, 'settings' | 'notifications'>
  label: string
  path: string
}[]

type PrimaryNavigationPath = (typeof NAV_ITEMS)[number]['path']

type PrimaryNavigationItemDefinition = {
  key: Exclude<NavigationItemKey, 'settings' | 'notifications'>
  shortLabel: string
  icon: 'layout' | 'users' | 'clock' | 'calendar' | 'wallet' | 'briefcase' | 'chart' | 'building'
  description: string
  section: Exclude<NavigationSectionKey, 'admin'>
  matcherPrefixes: string[]
}

const primaryNavigationDefinitions: Record<PrimaryNavigationPath, PrimaryNavigationItemDefinition> = {
  '/dashboard': {
    key: 'dashboard',
    shortLabel: 'Dashboard',
    icon: 'layout',
    description: 'Track workforce health, approvals, and operational priorities from one calm command center.',
    section: 'overview',
    matcherPrefixes: ['/dashboard'],
  },
  '/employees': {
    key: 'employees',
    shortLabel: 'Employees',
    icon: 'users',
    description: 'Manage employee records, search the directory, and move into detailed profiles without losing context.',
    section: 'workforce',
    matcherPrefixes: ['/employees'],
  },
  '/organization': {
    key: 'organization',
    shortLabel: 'Organization',
    icon: 'building',
    description: 'Review departments, role coverage, and staffing structure with clean organizational visibility.',
    section: 'workforce',
    matcherPrefixes: ['/organization', '/departments', '/roles'],
  },
  '/attendance': {
    key: 'attendance',
    shortLabel: 'Attendance',
    icon: 'clock',
    description: 'Monitor daily presence, identify exceptions, and keep time-tracking workflows aligned.',
    section: 'operations',
    matcherPrefixes: ['/attendance'],
  },
  '/leave': {
    key: 'leave',
    shortLabel: 'Leave',
    icon: 'calendar',
    description: 'Review leave requests, balances, and team coverage with consistent filters and approvals.',
    section: 'operations',
    matcherPrefixes: ['/leave', '/leave-requests'],
  },
  '/payroll': {
    key: 'payroll',
    shortLabel: 'Payroll',
    icon: 'wallet',
    description: 'Track payroll cycles, exceptions, and settlement readiness across the organization.',
    section: 'operations',
    matcherPrefixes: ['/payroll'],
  },
  '/hiring': {
    key: 'hiring',
    shortLabel: 'Hiring',
    icon: 'briefcase',
    description: 'Keep requisitions and candidate flow in one polished hiring workspace.',
    section: 'talent',
    matcherPrefixes: ['/hiring', '/job-postings', '/candidate-pipeline'],
  },
  '/performance': {
    key: 'performance',
    shortLabel: 'Performance',
    icon: 'chart',
    description: 'Review cycle progress, calibration status, and manager follow-up across the business.',
    section: 'talent',
    matcherPrefixes: ['/performance', '/performance-reviews'],
  },
}

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

export const primaryNavigationItems: NavigationItem[] = NAV_ITEMS.map((item) => {
  const definition = primaryNavigationDefinitions[item.path]

  return {
    ...definition,
    key: item.key,
    href: item.path,
    label: item.label,
  }
})

const utilityNavigationDefinitions: NavigationItem[] = [
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

export const navigationItems: NavigationItem[] = [...primaryNavigationItems, ...utilityNavigationDefinitions]

export const utilityNavigationItems = utilityNavigationDefinitions

export function isNavigationItemActive(pathname: string | undefined, item: NavigationItem) {
  if (!pathname) {
    return false
  }

  return item.matcherPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))
}

export function getNavigationItem(pathname: string | undefined) {
  return navigationItems.find((item) => isNavigationItemActive(pathname, item)) ?? navigationItems[0]
}
