export type NavigationSectionKey = 'overview' | 'people' | 'operations' | 'talent' | 'admin'

export type NavigationItem = {
  key:
    | 'dashboard'
    | 'employees'
    | 'departments'
    | 'roles'
    | 'employee_profile'
    | 'attendance'
    | 'leave'
    | 'payroll'
    | 'jobs'
    | 'candidates'
    | 'performance'
    | 'settings'
  href: string
  label: string
  shortLabel: string
  description: string
  section: NavigationSectionKey
  capabilityIds: string[]
  readModels: ReadModelKey[]
  showInSidebar?: boolean
}

export type ReadModelKey =
  | 'employee_directory_view'
  | 'attendance_dashboard_view'
  | 'leave_requests_view'
  | 'payroll_summary_view'
  | 'candidate_pipeline_view'
  | 'performance_review_view'
  | 'settings_configuration_view'

export const readModelLabels: Record<ReadModelKey, string> = {
  employee_directory_view: 'Employee Directory',
  attendance_dashboard_view: 'Attendance',
  leave_requests_view: 'Leave',
  payroll_summary_view: 'Payroll',
  candidate_pipeline_view: 'Candidates',
  performance_review_view: 'Performance',
  settings_configuration_view: 'Settings',
}

export function getReadModelLabel(readModel: ReadModelKey) {
  return readModelLabels[readModel]
}

export const navigationSections: { key: NavigationSectionKey; title: string }[] = [
  { key: 'overview', title: 'Overview' },
  { key: 'people', title: 'People' },
  { key: 'operations', title: 'Operations' },
  { key: 'talent', title: 'Talent' },
  { key: 'admin', title: 'Admin' },
]

export const navigationItems: NavigationItem[] = [
  {
    key: 'dashboard',
    href: '/',
    label: 'Dashboard',
    shortLabel: 'Dashboard',
    description: 'Cross-functional overview of workforce, attendance, leave, payroll, and hiring.',
    section: 'overview',
    capabilityIds: ['CAP-EMP-001', 'CAP-ATT-001', 'CAP-LEV-001', 'CAP-PAY-001', 'CAP-HIR-001', 'CAP-PRF-001'],
    readModels: [
      'employee_directory_view',
      'attendance_dashboard_view',
      'leave_requests_view',
      'payroll_summary_view',
      'candidate_pipeline_view',
      'performance_review_view',
    ],
  },
  {
    key: 'employees',
    href: '/employees',
    label: 'Employees',
    shortLabel: 'Employees',
    description: 'Directory of employees with search, filters, and records management.',
    section: 'people',
    capabilityIds: ['CAP-EMP-001'],
    readModels: ['employee_directory_view'],
  },
  {
    key: 'departments',
    href: '/departments',
    label: 'Departments',
    shortLabel: 'Departments',
    description: 'Department coverage, headcount, and staffing distribution.',
    section: 'people',
    capabilityIds: ['CAP-EMP-001'],
    readModels: ['employee_directory_view'],
  },
  {
    key: 'roles',
    href: '/roles',
    label: 'Roles',
    shortLabel: 'Roles',
    description: 'Role distribution, occupancy, and hiring concentration across the org.',
    section: 'people',
    capabilityIds: ['CAP-EMP-001'],
    readModels: ['employee_directory_view'],
  },
  {
    key: 'employee_profile',
    href: '/employee-profile',
    label: 'Employee Profile',
    shortLabel: 'Profile',
    description: 'Detailed employee record workspace for cross-functional HR workflows.',
    section: 'people',
    capabilityIds: ['CAP-EMP-002', 'CAP-ATT-001', 'CAP-LEV-001', 'CAP-PAY-001', 'CAP-PRF-001'],
    readModels: [
      'employee_directory_view',
      'attendance_dashboard_view',
      'leave_requests_view',
      'payroll_summary_view',
      'performance_review_view',
    ],
    showInSidebar: false,
  },
  {
    key: 'attendance',
    href: '/attendance',
    label: 'Attendance',
    shortLabel: 'Attendance',
    description: 'Attendance trends, exceptions, and day-to-day workforce visibility.',
    section: 'operations',
    capabilityIds: ['CAP-ATT-001', 'CAP-ATT-002'],
    readModels: ['attendance_dashboard_view'],
  },
  {
    key: 'leave',
    href: '/leave-requests',
    label: 'Leave',
    shortLabel: 'Leave',
    description: 'Requests, approvals, and team coverage for planned time away.',
    section: 'operations',
    capabilityIds: ['CAP-LEV-001', 'CAP-LEV-002'],
    readModels: ['leave_requests_view'],
  },
  {
    key: 'payroll',
    href: '/payroll',
    label: 'Payroll',
    shortLabel: 'Payroll',
    description: 'Pay periods, processing state, and payout summaries.',
    section: 'operations',
    capabilityIds: ['CAP-PAY-001', 'CAP-PAY-002'],
    readModels: ['payroll_summary_view'],
  },
  {
    key: 'jobs',
    href: '/job-postings',
    label: 'Jobs',
    shortLabel: 'Jobs',
    description: 'Open requisitions, openings, and posting health across teams.',
    section: 'talent',
    capabilityIds: ['CAP-HIR-001'],
    readModels: ['candidate_pipeline_view'],
  },
  {
    key: 'candidates',
    href: '/candidate-pipeline',
    label: 'Candidates',
    shortLabel: 'Candidates',
    description: 'Applications and interview pipeline progression for active hiring.',
    section: 'talent',
    capabilityIds: ['CAP-HIR-002'],
    readModels: ['candidate_pipeline_view'],
  },
  {
    key: 'performance',
    href: '/performance-reviews',
    label: 'Performance',
    shortLabel: 'Performance',
    description: 'Review cycle completion and performance management health.',
    section: 'talent',
    capabilityIds: ['CAP-PRF-001'],
    readModels: ['performance_review_view'],
  },
  {
    key: 'settings',
    href: '/settings',
    label: 'Settings',
    shortLabel: 'Settings',
    description: 'Global HRMS configuration for company info, policies, branding, and integrations.',
    section: 'admin',
    capabilityIds: ['CAP-ADM-001'],
    readModels: ['settings_configuration_view'],
  },
]

export const sidebarNavigationItems = navigationItems.filter((item) => item.showInSidebar !== false)
