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
import { Input } from '@/components/ui/input'
import { PageGrid, PageStack } from '@/components/ui/page'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

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

type PipelineRole = {
  title: string
  department: string
  applicants: number
  interviews: number
  stage: string
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
    hint: 'Distributed across 9 departments with 96% retention.',
    icon: Users,
  },
  {
    title: 'Monthly payroll',
    value: '$612,480',
    change: 'On track',
    hint: 'Next payroll closes on March 25 with zero unresolved exceptions.',
    icon: DollarSign,
  },
  {
    title: 'Open positions',
    value: '18',
    change: '6 priority roles',
    hint: 'Engineering and Sales hiring plans remain the top focus.',
    icon: BriefcaseBusiness,
  },
  {
    title: 'Attendance compliance',
    value: '97.8%',
    change: '+1.4%',
    hint: 'Late check-ins declined after the flexible shift policy update.',
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
]

const pipeline: PipelineRole[] = [
  {
    title: 'Senior Frontend Engineer',
    department: 'Engineering',
    applicants: 42,
    interviews: 6,
    stage: 'Final panel this week',
  },
  {
    title: 'HR Operations Specialist',
    department: 'People & Culture',
    applicants: 19,
    interviews: 4,
    stage: 'Offer review',
  },
  {
    title: 'Payroll Analyst',
    department: 'Finance',
    applicants: 27,
    interviews: 5,
    stage: 'Hiring manager screen',
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

const leaveRequests = [
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

const announcements = [
  'Medical insurance renewals are due for dependents by March 29.',
  'Managers should complete calibration notes before the April performance cycle freeze.',
  'Q2 headcount approvals for Customer Success and RevOps are ready for review.',
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
    <PageStack className="animate-[page-enter_180ms_ease-out] gap-6">
      <Card className="overflow-hidden border-slate-200 bg-white">
        <CardContent className="p-0">
          <div className="grid gap-6 p-6 lg:grid-cols-[minmax(0,1.5fr)_22rem] lg:p-8">
            <div className="space-y-5">
              <div className="flex flex-wrap items-center gap-3">
                <Badge>March workforce snapshot</Badge>
                <Badge variant="outline">Light enterprise workspace</Badge>
              </div>
              <div className="space-y-3">
                <h2 className="max-w-3xl text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                  HR operations built for headcount planning, performance visibility, and fast decision making.
                </h2>
                <p className="max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                  Track hiring, payroll readiness, leave approvals, and performance cycles from a clean command center designed for enterprise people teams.
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="w-full max-w-sm">
                  <Input aria-label="Search employees or teams" placeholder="Search employees, teams, or requests" />
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Button>
                    <UserPlus className="h-4 w-4" />
                    Add employee
                  </Button>
                  <Button variant="outline">
                    <FileCheck2 className="h-4 w-4" />
                    Review approvals
                  </Button>
                </div>
              </div>
            </div>

            <Card className="border-slate-200 bg-slate-50 shadow-none">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">Today&apos;s priorities</CardTitle>
                    <CardDescription>Focused items for the People Operations team.</CardDescription>
                  </div>
                  <Sparkles className="h-5 w-5 text-[var(--primary)]" />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-lg bg-blue-50 p-2 text-blue-700">
                      <Clock3 className="h-4 w-4" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-slate-900">Payroll cutoff in 2 days</p>
                      <p className="text-sm leading-6 text-slate-600">Finalize overtime approvals and sync reimbursement adjustments before 5:00 PM.</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-lg bg-green-50 p-2 text-green-700">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-slate-900">13 reviews ready for sign-off</p>
                      <p className="text-sm leading-6 text-slate-600">Most calibration notes are complete across Product, Finance, and Operations.</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-lg bg-amber-50 p-2 text-amber-700">
                      <CircleAlert className="h-4 w-4" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-slate-900">2 leave requests need coverage review</p>
                      <p className="text-sm leading-6 text-slate-600">Coordinate temporary ownership for Customer Support and Finance Operations.</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      <PageGrid className="gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon

          return (
            <Card key={metric.title} className="border-slate-200 bg-white">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="rounded-xl bg-blue-50 p-3 text-blue-700">
                    <Icon className="h-5 w-5" />
                  </div>
                  <Badge variant="outline">{metric.change}</Badge>
                </div>
                <div className="space-y-1">
                  <CardDescription>{metric.title}</CardDescription>
                  <CardTitle className="text-3xl">{metric.value}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-slate-600">{metric.hint}</p>
              </CardContent>
            </Card>
          )
        })}
      </PageGrid>

      <Tabs defaultValue="overview">
        <TabsList className="w-full justify-start bg-slate-100">
          <TabsTrigger value="overview">Workforce overview</TabsTrigger>
          <TabsTrigger value="hiring">Hiring pipeline</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_24rem]">
            <Card className="border-slate-200 bg-white">
              <CardHeader className="flex flex-col gap-3 border-b border-slate-200 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle className="text-xl">Team directory highlights</CardTitle>
                  <CardDescription>Current workforce view with role ownership and employee status.</CardDescription>
                </div>
                <Button variant="outline">
                  Open directory
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent className="px-0 pb-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {workforce.map((member) => (
                      <TableRow key={member.name}>
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
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card className="border-slate-200 bg-white">
                <CardHeader>
                  <CardTitle className="text-xl">Leave queue</CardTitle>
                  <CardDescription>Pending approvals that could impact staffing coverage.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {leaveRequests.map((request) => (
                    <div key={request.employee} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium text-slate-900">{request.employee}</p>
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

              <Card className="border-slate-200 bg-white">
                <CardHeader>
                  <CardTitle className="text-xl">Internal announcements</CardTitle>
                  <CardDescription>Time-sensitive reminders from HR, payroll, and leadership.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {announcements.map((announcement) => (
                    <div key={announcement} className="flex gap-3 rounded-xl border border-slate-200 p-4">
                      <CalendarClock className="mt-0.5 h-4 w-4 text-blue-700" />
                      <p className="text-sm leading-6 text-slate-600">{announcement}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="hiring">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,0.9fr)]">
            <Card className="border-slate-200 bg-white">
              <CardHeader className="border-b border-slate-200">
                <CardTitle className="text-xl">Priority hiring roles</CardTitle>
                <CardDescription>Open requisitions aligned to current approved headcount plans.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-5">
                {pipeline.map((role) => (
                  <div key={role.title} className="rounded-xl border border-slate-200 p-5">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="text-base font-semibold text-slate-950">{role.title}</p>
                        <p className="text-sm text-slate-500">{role.department}</p>
                      </div>
                      <Badge>{role.stage}</Badge>
                    </div>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-sm text-slate-500">Applicants</p>
                        <p className="mt-1 text-2xl font-semibold text-slate-950">{role.applicants}</p>
                      </div>
                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-sm text-slate-500">Interview loops</p>
                        <p className="mt-1 text-2xl font-semibold text-slate-950">{role.interviews}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white">
              <CardHeader>
                <CardTitle className="text-xl">Hiring health</CardTitle>
                <CardDescription>Operational signals from recruiting and coordination workflows.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-xl border border-slate-200 bg-blue-50/60 p-4">
                  <div className="flex items-center gap-3">
                    <TrendingUp className="h-5 w-5 text-blue-700" />
                    <div>
                      <p className="font-medium text-slate-900">Time to fill</p>
                      <p className="text-sm text-slate-600">Average reduced to 29 days across enterprise roles.</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-green-50/60 p-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-green-700" />
                    <div>
                      <p className="font-medium text-slate-900">Offer acceptance</p>
                      <p className="text-sm text-slate-600">91% acceptance rate in the last 60 days.</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-amber-50/60 p-4">
                  <div className="flex items-center gap-3">
                    <CircleAlert className="h-5 w-5 text-amber-700" />
                    <div>
                      <p className="font-medium text-slate-900">Interviewer capacity</p>
                      <p className="text-sm text-slate-600">Engineering panels are nearing capacity for next week.</p>
                    </div>
                  </div>
                </div>
                <Button className="w-full" variant="outline">
                  View recruiting analytics
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.95fr)]">
            <Card className="border-slate-200 bg-white">
              <CardHeader className="border-b border-slate-200">
                <CardTitle className="text-xl">Review cycle tracker</CardTitle>
                <CardDescription>Manager and calibration readiness for the current cycle.</CardDescription>
              </CardHeader>
              <CardContent className="px-0 pb-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead>Manager</TableHead>
                      <TableHead>Due date</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reviews.map((review) => (
                      <TableRow key={review.name}>
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

            <Card className="border-slate-200 bg-white">
              <CardHeader>
                <CardTitle className="text-xl">Cycle readiness</CardTitle>
                <CardDescription>Completion indicators before ratings are finalized.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-slate-700">Self reviews submitted</p>
                    <p className="text-lg font-semibold text-slate-950">88%</p>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-blue-600" style={{ width: '88%' }} />
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-slate-700">Manager reviews completed</p>
                    <p className="text-lg font-semibold text-slate-950">74%</p>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-emerald-600" style={{ width: '74%' }} />
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-slate-700">Calibration completed</p>
                    <p className="text-lg font-semibold text-slate-950">61%</p>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-amber-500" style={{ width: '61%' }} />
                  </div>
                </div>
                <Button className="w-full">
                  Continue review cycle
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </PageStack>
  )
}
