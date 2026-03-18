export type NavigationItem = {
  key:
    | 'dashboard'
    | 'employee_list'
    | 'employee_profile'
    | 'attendance_dashboard'
    | 'leave_requests'
    | 'payroll_dashboard'
    | 'job_postings'
    | 'candidate_pipeline'
    | 'performance_reviews'
  href: string
  label: string
  shortLabel: string
  description: string
  capabilityIds: string[]
  readModels: ReadModelKey[]
}

export type ReadModelKey =
  | 'employee_directory_view'
  | 'attendance_dashboard_view'
  | 'leave_requests_view'
  | 'payroll_summary_view'
  | 'candidate_pipeline_view'
  | 'performance_review_view'

export const readModelLabels: Record<ReadModelKey, string> = {
  employee_directory_view: 'Employee Directory',
  attendance_dashboard_view: 'Attendance',
  leave_requests_view: 'Leave',
  payroll_summary_view: 'Payroll',
  candidate_pipeline_view: 'Candidates',
  performance_review_view: 'Performance',
}

export function getReadModelLabel(readModel: ReadModelKey) {
  return readModelLabels[readModel]
}

export const navigationItems: NavigationItem[] = [
  {
    key: 'dashboard',
    href: '/',
    label: 'Dashboard',
    shortLabel: 'Dashboard',
    description: 'Cross-functional operational overview.',
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
    key: 'employee_list',
    href: '/employees',
    label: 'Employee List',
    shortLabel: 'Employees',
    description: 'Directory of employees, departments, and roles.',
    capabilityIds: ['CAP-EMP-001'],
    readModels: ['employee_directory_view'],
  },
  {
    key: 'employee_profile',
    href: '/employee-profile',
    label: 'Employee Profile',
    shortLabel: 'Profiles',
    description: '360° employee detail surface for HR operations.',
    capabilityIds: ['CAP-EMP-002', 'CAP-ATT-001', 'CAP-LEV-001', 'CAP-PAY-001', 'CAP-PRF-001'],
    readModels: [
      'employee_directory_view',
      'attendance_dashboard_view',
      'leave_requests_view',
      'payroll_summary_view',
      'performance_review_view',
    ],
  },
  {
    key: 'attendance_dashboard',
    href: '/attendance',
    label: 'Attendance Dashboard',
    shortLabel: 'Attendance',
    description: 'Attendance trends, states, and exceptions.',
    capabilityIds: ['CAP-ATT-001', 'CAP-ATT-002'],
    readModels: ['attendance_dashboard_view'],
  },
  {
    key: 'leave_requests',
    href: '/leave-requests',
    label: 'Leave Requests',
    shortLabel: 'Leave',
    description: 'Submission, approvals, and team coverage view.',
    capabilityIds: ['CAP-LEV-001', 'CAP-LEV-002'],
    readModels: ['leave_requests_view'],
  },
  {
    key: 'payroll_dashboard',
    href: '/payroll',
    label: 'Payroll Dashboard',
    shortLabel: 'Payroll',
    description: 'Payroll periods, status, and payout summaries.',
    capabilityIds: ['CAP-PAY-001', 'CAP-PAY-002'],
    readModels: ['payroll_summary_view'],
  },
  {
    key: 'job_postings',
    href: '/job-postings',
    label: 'Job Postings',
    shortLabel: 'Jobs',
    description: 'Open requisitions by department and role.',
    capabilityIds: ['CAP-HIR-001'],
    readModels: ['candidate_pipeline_view'],
  },
  {
    key: 'candidate_pipeline',
    href: '/candidate-pipeline',
    label: 'Candidate Pipeline',
    shortLabel: 'Pipeline',
    description: 'Applications and interview pipeline progression.',
    capabilityIds: ['CAP-HIR-002'],
    readModels: ['candidate_pipeline_view'],
  },
  {
    key: 'performance_reviews',
    href: '/performance-reviews',
    label: 'Performance Reviews',
    shortLabel: 'Reviews',
    description: 'Review cycle health and completion status.',
    capabilityIds: ['CAP-PRF-001'],
    readModels: ['performance_review_view'],
  },
]
