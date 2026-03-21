'use client'

import {
  ArrowRight,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  CircleAlert,
  Clock3,
  DollarSign,
  ShieldCheck,
  TrendingUp,
  UserPlus,
  Users,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  PageSection,
  PageSectionHeader,
  PageStack,
  pageSectionBodyClassName,
  pageEyebrowClassName,
  pageIconChipClassName,
  pageMetaTextClassName,
  pageSectionTitleClassName,
} from '@/components/ui/page'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

type MetricCard = {
  title: string
  value: string
  change: string
  hint: string
  icon: typeof Users
}

type TeamMember = {
  name: string
  role: string
  department: string
  location: string
  status: 'Active' | 'On leave' | 'Probation'
}

type PriorityItem = {
  title: string
  description: string
  urgency: string
  icon: typeof Clock3
  tone: string
}

type LeaveRequest = {
  employee: string
  type: string
  dates: string
  manager: string
  priority: string
}

type ReviewItem = {
  name: string
  manager: string
  dueDate: string
  status: 'Ready' | 'In progress' | 'Needs calibration'
}

const metrics: MetricCard[] = [
  {
    title: 'Active employees',
    value: '248',
    change: '+12 this quarter',
    hint: '96% retention across 9 departments.',
    icon: Users,
  },
  {
    title: 'Monthly payroll',
    value: '$612,480',
    change: 'Closes Mar 25',
    hint: 'Zero unresolved payroll exceptions.',
    icon: DollarSign,
  },
  {
    title: 'Open positions',
    value: '18',
    change: '6 urgent roles',
    hint: 'Engineering and Sales remain highest priority.',
    icon: BriefcaseBusiness,
  },
  {
    title: 'Attendance compliance',
    value: '97.8%',
    change: '+1.4% MoM',
    hint: 'Late check-ins continue to trend down.',
    icon: ShieldCheck,
  },
]

const workforce: TeamMember[] = [
  {
    name: 'Ayesha Khan',
    role: 'Senior Product Designer',
    department: 'Product Design',
    location: 'Dubai · Hybrid',
    status: 'Active',
  },
  {
    name: 'Omar Siddiqui',
    role: 'Finance Operations Lead',
    department: 'Finance',
    location: 'Lahore · On-site',
    status: 'Active',
  },
  {
    name: 'Maham Raza',
    role: 'People Business Partner',
    department: 'People & Culture',
    location: 'Karachi · Hybrid',
    status: 'On leave',
  },
  {
    name: 'Danish Ali',
    role: 'Account Executive',
    department: 'Sales',
    location: 'Riyadh · Remote',
    status: 'Probation',
  },
  {
    name: 'Sara Javed',
    role: 'Talent Acquisition Partner',
    department: 'People & Culture',
    location: 'Islamabad · Hybrid',
    status: 'Active',
  },
]

const priorities: PriorityItem[] = [
  {
    title: 'Payroll cutoff in 2 days',
    description: 'Finalize overtime approvals and reimbursement adjustments before 5:00 PM.',
    urgency: 'Urgent · Finance coordination',
    icon: Clock3,
    tone: 'text-blue-700',
  },
  {
    title: '13 reviews ready for sign-off',
    description: 'Calibration notes are complete across Product, Finance, and Operations.',
    urgency: 'Today · Approval queue',
    icon: CheckCircle2,
    tone: 'text-emerald-700',
  },
  {
    title: 'Coverage review needed',
    description: 'Two leave requests impact Customer Support and Finance operations this week.',
    urgency: 'Needs attention · Staffing risk',
    icon: CircleAlert,
    tone: 'text-amber-700',
  },
  {
    title: 'Priority hiring panels blocked',
    description: 'Engineering interview loops are at capacity for next week’s final panels.',
    urgency: 'Escalate · Hiring velocity',
    icon: BriefcaseBusiness,
    tone: 'text-rose-700',
  },
]

const leaveRequests: LeaveRequest[] = [
  {
    employee: 'Noor Ahmed',
    type: 'Annual leave',
    dates: 'Mar 28 – Apr 1',
    manager: 'Ayesha Malik',
    priority: 'Low risk',
  },
  {
    employee: 'Bilal Hussain',
    type: 'Sick leave',
    dates: 'Mar 20 – Mar 21',
    manager: 'Usman Farooq',
    priority: 'Coverage required',
  },
  {
    employee: 'Rida Ameen',
    type: 'Parental leave',
    dates: 'Apr 8 – Jul 5',
    manager: 'Sameer Azhar',
    priority: 'Transition planning',
  },
]

const reviews: ReviewItem[] = [
  {
    name: 'Zara Sheikh',
    manager: 'Imran Qureshi',
    dueDate: 'Mar 22',
    status: 'Ready',
  },
  {
    name: 'Saad Noman',
    manager: 'Fatima Rehman',
    dueDate: 'Mar 24',
    status: 'In progress',
  },
  {
    name: 'Hina Tariq',
    manager: 'Ali Hamza',
    dueDate: 'Mar 26',
    status: 'Needs calibration',
  },
]

const directoryHighlights = [
  {
    team: 'People Operations',
    update: '3 onboarding cohorts start Monday with documents 100% complete.',
  },
  {
    team: 'Finance',
    update: 'Payroll exceptions cleared for all but one reimbursement case.',
  },
  {
    team: 'Customer Support',
    update: 'Backfill coverage plan is needed for two pending leave requests.',
  },
]

const sectionLabelClassName = pageEyebrowClassName
const sectionTitleClassName = pageSectionTitleClassName
const sectionBodyClassName = pageSectionBodyClassName
const mutedMetaClassName = pageMetaTextClassName

function statusBadge(status: TeamMember['status'] | ReviewItem['status']) {
  if (status === 'Active' || status === 'Ready') {
    return <Badge variant="success">{status}</Badge>
  }

  if (status === 'On leave' || status === 'In progress') {
    return <Badge variant="warning">{status}</Badge>
  }

  return <Badge variant="danger">{status}</Badge>
}

export function EnterpriseDashboard() {
  return (
    <PageStack className="animate-[page-enter_180ms_ease-out] gap-6">
      <PageSection>
        <PageSectionHeader
          eyebrow="Dashboard workspace"
          title="Today&apos;s workforce command center"
          description="Monitor workforce health, clear approvals, and keep payroll, hiring, and coverage decisions moving from one structured operating view."
          actions={
            <Button size="lg" className="w-full justify-between sm:w-auto sm:min-w-56">
              <span className="inline-flex items-center gap-2">
                <UserPlus className="h-4 w-4" />
                Add employee
              </span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          }
          badge={
            <div className="flex flex-wrap items-center gap-2">
              <Badge>March workforce snapshot</Badge>
              <Badge variant="outline">Command center</Badge>
            </div>
          }
        />
      </PageSection>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-12">
        {metrics.map((metric) => {
          const Icon = metric.icon

          return (
            <Card key={metric.title} className="flex min-h-48 flex-col xl:col-span-3">
              <CardContent className="flex h-full flex-col justify-between p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className={pageIconChipClassName}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <p className={mutedMetaClassName}>{metric.change}</p>
                </div>

                <div className="space-y-3">
                  <p className="text-sm font-medium text-slate-600">{metric.title}</p>
                  <p className="text-3xl font-semibold tracking-tight text-slate-950">{metric.value}</p>
                  <p className="text-sm leading-6 text-slate-500">{metric.hint}</p>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-12">
        <div className="min-w-0 space-y-6 xl:col-span-8">
          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-4 sm:flex-row sm:items-end sm:justify-between">
              <div className="space-y-3">
                <div className="space-y-1">
                  <p className={sectionLabelClassName}>Primary workspace</p>
                  <CardTitle className="text-2xl">Workforce overview</CardTitle>
                </div>
                <p className="max-w-2xl text-sm leading-6 text-slate-600">
                  Review role ownership, status, and location from one operating table built for fast scanning.
                </p>
              </div>
              <Button variant="ghost" className="w-full justify-start px-0 text-slate-600 sm:w-auto sm:justify-center sm:px-3.5">
                Open directory
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardHeader>

            <div className="overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-200">
                    <TableHead>Employee</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workforce.map((member) => (
                    <TableRow key={member.name} className="border-slate-200/80">
                      <TableCell>
                        <div className="space-y-1">
                          <p className="font-medium text-slate-900">{member.name}</p>
                          <p className="text-sm text-slate-500">{member.role}</p>
                        </div>
                      </TableCell>
                      <TableCell>{member.department}</TableCell>
                      <TableCell>{member.location}</TableCell>
                      <TableCell>{statusBadge(member.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </Card>

          <div className="grid gap-6 lg:grid-cols-12">
            <Card className="lg:col-span-7">
              <CardHeader className="gap-3 p-4">
                <div className="space-y-1">
                  <p className={sectionLabelClassName}>Activity</p>
                  <h3 className={sectionTitleClassName}>Operational signals</h3>
                </div>
              </CardHeader>

              <CardContent className="space-y-4 px-4 pb-4">
                {directoryHighlights.map((highlight) => (
                  <div key={highlight.team} className="space-y-2 border-b border-slate-200 pb-4 last:border-b-0 last:pb-0">
                    <p className="text-sm font-medium text-slate-900">{highlight.team}</p>
                    <p className={sectionBodyClassName}>{highlight.update}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="lg:col-span-5">
              <CardHeader className="gap-3 p-4">
                <div className="space-y-1">
                  <p className={sectionLabelClassName}>Performance pulse</p>
                  <h3 className={sectionTitleClassName}>Cycle momentum</h3>
                </div>
              </CardHeader>

              <CardContent className="space-y-4 px-4 pb-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm text-slate-600">Self reviews submitted</p>
                      <p className="text-sm font-semibold text-slate-950">88%</p>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200">
                      <div className="h-2 rounded-full bg-blue-600" style={{ width: '88%' }} />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm text-slate-600">Manager reviews completed</p>
                      <p className="text-sm font-semibold text-slate-950">74%</p>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200">
                      <div className="h-2 rounded-full bg-emerald-600" style={{ width: '74%' }} />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm text-slate-600">Calibration completed</p>
                      <p className="text-sm font-semibold text-slate-950">61%</p>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200">
                      <div className="h-2 rounded-full bg-amber-500" style={{ width: '61%' }} />
                    </div>
                  </div>
                </div>

                <div className="space-y-3 border-t border-slate-200 pt-4">
                  <div className="flex gap-3">
                    <TrendingUp className="mt-0.5 h-4 w-4 text-blue-700" />
                    <p className={sectionBodyClassName}>
                      13 reviews are ready for sign-off and 7 still need calibration alignment.
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <CalendarClock className="mt-0.5 h-4 w-4 text-emerald-700" />
                    <p className={sectionBodyClassName}>
                      Managers should complete calibration notes before the April performance freeze.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <aside className="space-y-4 xl:col-span-4">
          <Card className="bg-[var(--surface-subtle)] shadow-none">
            <CardHeader className="gap-3 p-4">
              <div className="space-y-1">
                <p className={sectionLabelClassName}>Priorities</p>
                <h2 className="text-xl font-semibold tracking-tight text-slate-950">Today&apos;s action queue</h2>
              </div>
              <p className={sectionBodyClassName}>
                Urgent approvals, staffing risks, and blocked work surfaced for immediate action.
              </p>
            </CardHeader>

            <CardContent className="space-y-4 px-4 pb-4">
              {priorities.map((item) => {
                const Icon = item.icon

                return (
                  <div key={item.title} className="space-y-3 border-b border-slate-200 pb-4 last:border-b-0 last:pb-0">
                    <div className="flex items-start gap-3">
                      <div className={`rounded-[var(--radius-control)] bg-white p-2 ring-1 ring-slate-200 ${item.tone}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 space-y-1">
                        <p className="text-sm font-medium text-slate-900">{item.title}</p>
                        <p className={mutedMetaClassName}>{item.urgency}</p>
                      </div>
                    </div>
                    <p className={sectionBodyClassName}>{item.description}</p>
                  </div>
                )
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-3 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-slate-900">Approval queue</p>
                  <p className="text-sm text-slate-500">3 items need action this week</p>
                </div>
                <Badge variant="outline">This week</Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-3 px-4 pb-4">
              {reviews.map((review) => (
                <div key={review.name} className="flex items-center justify-between gap-3 border-t border-slate-200 pt-3 first:border-t-0 first:pt-0">
                  <div className="min-w-0 space-y-1">
                    <p className="text-sm font-medium text-slate-900">{review.name}</p>
                    <p className="text-xs text-slate-500">
                      {review.manager} · Due {review.dueDate}
                    </p>
                  </div>
                  {statusBadge(review.status)}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-3 p-4">
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-900">Leave coverage watch</p>
                <p className="text-sm text-slate-500">Upcoming requests that affect staffing continuity</p>
              </div>
            </CardHeader>

            <CardContent className="space-y-3 px-4 pb-4">
              {leaveRequests.map((request) => (
                <div key={request.employee} className="space-y-2 border-t border-slate-200 pt-3 first:border-t-0 first:pt-0">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-slate-900">{request.employee}</p>
                      <p className="text-sm text-slate-500">{request.type}</p>
                    </div>
                    <Badge variant="outline">{request.priority}</Badge>
                  </div>
                  <p className="text-sm text-slate-600">{request.dates}</p>
                  <p className="text-xs text-slate-500">Manager: {request.manager}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </aside>
      </section>
    </PageStack>
  )
}
