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
  label: string
  description: string
  capabilityIds: string[]
  readModels: string[]
}

export const navigationItems: NavigationItem[] = [
  {
    key: 'dashboard',
    label: 'Dashboard',
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
    label: 'Employee List',
    description: 'Directory of employees, departments, and roles.',
    capabilityIds: ['CAP-EMP-001'],
    readModels: ['employee_directory_view'],
  },
  {
    key: 'employee_profile',
    label: 'Employee Profile',
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
    label: 'Attendance Dashboard',
    description: 'Attendance trends, states, and exceptions.',
    capabilityIds: ['CAP-ATT-001', 'CAP-ATT-002'],
    readModels: ['attendance_dashboard_view'],
  },
  {
    key: 'leave_requests',
    label: 'Leave Requests',
    description: 'Submission, approvals, and team coverage view.',
    capabilityIds: ['CAP-LEV-001', 'CAP-LEV-002'],
    readModels: ['leave_requests_view'],
  },
  {
    key: 'payroll_dashboard',
    label: 'Payroll Dashboard',
    description: 'Payroll periods, status, and payout summaries.',
    capabilityIds: ['CAP-PAY-001', 'CAP-PAY-002'],
    readModels: ['payroll_summary_view'],
  },
  {
    key: 'job_postings',
    label: 'Job Postings',
    description: 'Open requisitions by department and role.',
    capabilityIds: ['CAP-HIR-001'],
    readModels: ['candidate_pipeline_view'],
  },
  {
    key: 'candidate_pipeline',
    label: 'Candidate Pipeline',
    description: 'Applications and interview pipeline progression.',
    capabilityIds: ['CAP-HIR-002'],
    readModels: ['candidate_pipeline_view'],
  },
  {
    key: 'performance_reviews',
    label: 'Performance Reviews',
    description: 'Review cycle health and completion status.',
    capabilityIds: ['CAP-PRF-001'],
    readModels: ['performance_review_view'],
  },
]
