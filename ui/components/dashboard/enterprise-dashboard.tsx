'use client'

import {
  ArrowRight,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  CircleAlert,
  Clock3,
  DollarSign,
  FileCheck2,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  UserPlus,
  Users,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PageGrid, PageStack } from '@/components/ui/page'
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
    tone: 'bg-blue-50 text-blue-700',
  },
  {
    title: '13 reviews ready for sign-off',
    description: 'Calibration notes are complete across Product, Finance, and Operations.',
    urgency: 'Today · Approval queue',
    icon: CheckCircle2,
    tone: 'bg-emerald-50 text-emerald-700',
  },
  {
    title: 'Coverage review needed',
    description: 'Two leave requests impact Customer Support and Finance operations this week.',
    urgency: 'Needs attention · Staffing risk',
    icon: CircleAlert,
    tone: 'bg-amber-50 text-amber-700',
  },
  {
    title: 'Priority hiring panels blocked',
    description: 'Engineering interview loops are at capacity for next week’s final panels.',
    urgency: 'Escalate · Hiring velocity',
    icon: BriefcaseBusiness,
    tone: 'bg-rose-50 text-rose-700',
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

function statusBadge(status: TeamMember['status'] | ReviewItem['status']) {
  if (status === 'Active' || status === 'Ready') {
    return <Badge variant="success">{status}</Badge>
  }

  if (status === 'On leave' || status === 'In progress') {
    return <Badge className="bg-amber-50 text-amber-700">{status}</Badge>
  }

  return <Badge className="bg-red-50 text-red-700">{status}</Badge>
}

export function EnterpriseDashboard() {
  return (
    <PageStack className="animate-[page-enter_180ms_ease-out] gap-8">
      <section className="grid gap-6 rounded-[1.75rem] bg-white px-6 py-6 shadow-sm ring-1 ring-slate-200/70 lg:grid-cols-[minmax(0,1.6fr)_auto] lg:items-start lg:px-8 lg:py-8">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge>March workforce snapshot</Badge>
            <Badge variant="outline">Command center</Badge>
          </div>
          <div className="space-y-3">
            <h2 className="max-w-4xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Run workforce operations from one decision-ready HR command center.
            </h2>
            <p className="max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
              Scan workforce health, unblock approvals, and move payroll, hiring, and performance work forward without losing today&apos;s priorities.
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3 lg:min-w-64 lg:items-end">
          <Button className="w-full lg:w-auto">
            <UserPlus className="h-4 w-4" />
            Add employee
          </Button>
          <Button variant="ghost" className="w-full justify-center lg:w-auto">
            <FileCheck2 className="h-4 w-4" />
            Review approvals
          </Button>
        </div>
      </section>

      <PageGrid className="gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon

          return (
            <Card key={metric.title} className="border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
              <CardContent className="flex h-full flex-col gap-4 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="rounded-xl bg-slate-100 p-2.5 text-slate-700">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-medium text-slate-500">{metric.change}</span>
                </div>
                <div className="space-y-1">
                  <p className="text-3xl font-semibold tracking-tight text-slate-950">{metric.value}</p>
                  <p className="text-sm font-medium text-slate-700">{metric.title}</p>
                  <p className="text-xs leading-5 text-slate-500">{metric.hint}</p>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </PageGrid>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.9fr)_minmax(18rem,0.8fr)]">
        <div className="space-y-4 rounded-[1.5rem] bg-white px-0 py-0 ring-1 ring-slate-200/70">
          <div className="flex flex-col gap-4 border-b border-slate-200/80 px-6 py-5 sm:flex-row sm:items-end sm:justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Primary workspace</p>
              <h3 className="text-2xl font-semibold tracking-tight text-slate-950">Workforce overview</h3>
              <p className="text-sm leading-6 text-slate-600">Track team coverage, role ownership, and employee status with a high-readability working view.</p>
            </div>
            <Button variant="outline">
              Open directory
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          <div className="px-0 pb-2">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200/80">
                  <TableHead>Employee</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workforce.map((member) => (
                  <TableRow key={member.name} className="border-slate-200/70">
                    <TableCell>
                      <div>
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
        </div>

        <Card className="border-0 bg-slate-950 text-white shadow-sm">
          <CardHeader className="space-y-3 pb-2">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardDescription className="text-slate-300">Priority panel</CardDescription>
                <CardTitle className="text-2xl text-white">Today&apos;s priorities</CardTitle>
              </div>
              <Sparkles className="h-5 w-5 text-slate-200" />
            </div>
            <p className="text-sm leading-6 text-slate-300">Approval queue, urgent items, and operational blockers surfaced for immediate action.</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {priorities.map((item) => {
              const Icon = item.icon

              return (
                <div key={item.title} className="rounded-2xl bg-white/8 p-4 ring-1 ring-white/10">
                  <div className="flex items-start gap-3">
                    <div className={`rounded-xl p-2.5 ${item.tone}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 space-y-1.5">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-semibold text-white">{item.title}</p>
                        <span className="text-xs text-slate-400">{item.urgency}</span>
                      </div>
                      <p className="text-sm leading-6 text-slate-300">{item.description}</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      </section>

      <PageGrid className="gap-4 xl:grid-cols-3">
        <Card className="border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardHeader className="pb-3">
            <CardDescription>Supporting data</CardDescription>
            <CardTitle className="text-lg">Team directory highlights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {directoryHighlights.map((highlight) => (
              <div key={highlight.team} className="rounded-xl bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-900">{highlight.team}</p>
                <p className="mt-1 text-sm leading-6 text-slate-600">{highlight.update}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardHeader className="pb-3">
            <CardDescription>Supporting data</CardDescription>
            <CardTitle className="text-lg">Leave queue</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {leaveRequests.map((request) => (
              <div key={request.employee} className="rounded-xl bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{request.employee}</p>
                    <p className="text-sm text-slate-500">{request.type}</p>
                  </div>
                  <Badge variant="outline">{request.priority}</Badge>
                </div>
                <div className="mt-3 space-y-1 text-sm text-slate-600">
                  <p>{request.dates}</p>
                  <p>Manager: {request.manager}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardHeader className="pb-3">
            <CardDescription>Supporting data</CardDescription>
            <CardTitle className="text-lg">Performance snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-xl bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-slate-700">Self reviews submitted</p>
                <p className="text-lg font-semibold text-slate-950">88%</p>
              </div>
              <div className="mt-3 h-2 rounded-full bg-slate-200">
                <div className="h-2 rounded-full bg-blue-600" style={{ width: '88%' }} />
              </div>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-slate-700">Manager reviews completed</p>
                <p className="text-lg font-semibold text-slate-950">74%</p>
              </div>
              <div className="mt-3 h-2 rounded-full bg-slate-200">
                <div className="h-2 rounded-full bg-emerald-600" style={{ width: '74%' }} />
              </div>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-slate-700">Calibration completed</p>
                <p className="text-lg font-semibold text-slate-950">61%</p>
              </div>
              <div className="mt-3 h-2 rounded-full bg-slate-200">
                <div className="h-2 rounded-full bg-amber-500" style={{ width: '61%' }} />
              </div>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <div className="flex items-start gap-3">
                <TrendingUp className="mt-0.5 h-4 w-4 text-blue-700" />
                <div>
                  <p className="text-sm font-medium text-slate-900">Cycle momentum</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">13 reviews are ready for sign-off and 7 still need calibration alignment.</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </PageGrid>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.9fr)]">
        <Card className="border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardHeader className="pb-3">
            <CardDescription>Secondary workspace</CardDescription>
            <CardTitle className="text-lg">Approval queue</CardTitle>
          </CardHeader>
          <CardContent className="px-0 pb-2">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200/80">
                  <TableHead>Employee</TableHead>
                  <TableHead>Manager</TableHead>
                  <TableHead>Due date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reviews.map((review) => (
                  <TableRow key={review.name} className="border-slate-200/70">
                    <TableCell className="font-medium text-slate-900">{review.name}</TableCell>
                    <TableCell>{review.manager}</TableCell>
                    <TableCell>{review.dueDate}</TableCell>
                    <TableCell>{statusBadge(review.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardHeader className="pb-3">
            <CardDescription>Signals</CardDescription>
            <CardTitle className="text-lg">Operational reminders</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-3 rounded-xl bg-slate-50 p-4">
              <CalendarClock className="mt-0.5 h-4 w-4 text-blue-700" />
              <p className="text-sm leading-6 text-slate-600">Medical insurance renewals are due for dependents by March 29.</p>
            </div>
            <div className="flex gap-3 rounded-xl bg-slate-50 p-4">
              <FileCheck2 className="mt-0.5 h-4 w-4 text-emerald-700" />
              <p className="text-sm leading-6 text-slate-600">Managers should complete calibration notes before the April performance cycle freeze.</p>
            </div>
            <div className="flex gap-3 rounded-xl bg-slate-50 p-4">
              <BriefcaseBusiness className="mt-0.5 h-4 w-4 text-amber-700" />
              <p className="text-sm leading-6 text-slate-600">Q2 headcount approvals for Customer Success and RevOps are ready for review.</p>
            </div>
          </CardContent>
        </Card>
      </section>
    </PageStack>
  )
}
