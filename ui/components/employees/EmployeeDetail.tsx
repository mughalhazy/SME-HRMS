'use client'

import Link from 'next/link'
import {
  Activity,
  ArrowLeft,
  BriefcaseBusiness,
  CalendarClock,
  FileText,
  Mail,
  MapPin,
  Pencil,
  Phone,
  ShieldCheck,
  UserRound,
  Wallet,
} from 'lucide-react'

import { employees, getEmployeeById, getEmployeeInitials } from '@/components/employees/employee-data'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

function statusBadgeClass(status: string) {
  switch (status) {
    case 'Active':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    case 'Remote':
      return 'bg-sky-50 text-sky-700 border-sky-200'
    case 'On Leave':
      return 'bg-amber-50 text-amber-700 border-amber-200'
    default:
      return 'bg-rose-50 text-rose-700 border-rose-200'
  }
}

export function EmployeeDetail({ employeeId }: { employeeId?: string }) {
  const employee = getEmployeeById(employeeId ?? '') ?? employees[0]

  const stats = [
    { label: 'Attendance %', value: employee.attendanceRate, note: 'Present and punctual across current reporting cycle.' },
    { label: 'Leaves taken', value: employee.leavesTaken, note: 'Approved leave days used in the current annual cycle.' },
    { label: 'Salary band', value: employee.salaryBand, note: 'Current compensation tier aligned with role level.' },
    { label: 'Performance score', value: employee.performanceScore, note: 'Latest calibrated review snapshot.' },
  ]

  const overviewSections = [
    {
      title: 'Personal info',
      description: 'Core employee identity and profile details.',
      items: [
        { label: 'Full name', value: employee.name },
        { label: 'Employee ID', value: employee.id },
        { label: 'Work email', value: employee.email },
        { label: 'Phone', value: employee.phone },
      ],
    },
    {
      title: 'Job info',
      description: 'Current position, reporting line, and employment details.',
      items: [
        { label: 'Role', value: employee.role },
        { label: 'Department', value: employee.department },
        { label: 'Manager', value: employee.manager },
        { label: 'Employment type', value: employee.employmentType },
      ],
    },
    {
      title: 'Location & support',
      description: 'Location data and key contact references.',
      items: [
        { label: 'Location', value: employee.location },
        { label: 'Emergency contact', value: employee.emergencyContact },
        { label: 'Joined', value: new Intl.DateTimeFormat('en-US', { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(employee.joinDate)) },
        { label: 'Status', value: employee.status },
      ],
    },
  ]

  const secondaryTabs = [
    {
      value: 'attendance',
      title: 'Attendance summary',
      description: `${employee.attendanceRate} attendance with healthy punctuality trends over the current quarter.`,
      icon: CalendarClock,
    },
    {
      value: 'leave',
      title: 'Leave balance',
      description: `${employee.leavesTaken} leave days used with no pending exceptions requiring HR intervention.`,
      icon: ShieldCheck,
    },
    {
      value: 'payroll',
      title: 'Payroll snapshot',
      description: `Salary band ${employee.salaryBand} is active and payroll records are synced for the current cycle.`,
      icon: Wallet,
    },
    {
      value: 'documents',
      title: 'Document center',
      description: 'Employment documents, verification records, and compliance files remain in a healthy state.',
      icon: FileText,
    },
    {
      value: 'activity',
      title: 'Recent activity',
      description: 'Recent updates include profile changes, attendance review, and scheduled manager touchpoints.',
      icon: Activity,
    },
  ]

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="space-y-6 p-6 lg:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
            <div className="space-y-5">
              <Button asChild variant="ghost" className="-ml-3 w-fit text-slate-600 hover:bg-slate-100 hover:text-slate-950">
                <Link href="/employees">
                  <ArrowLeft className="h-4 w-4" />
                  Back to employees
                </Link>
              </Button>

              <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
                <Avatar className="h-20 w-20 border border-slate-200 bg-slate-50">
                  <AvatarFallback className="bg-slate-100 text-xl font-semibold text-slate-700">{getEmployeeInitials(employee.name)}</AvatarFallback>
                </Avatar>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-3xl font-semibold tracking-tight text-slate-950">{employee.name}</h2>
                      <Badge variant="outline" className={statusBadgeClass(employee.status)}>
                        {employee.status}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
                      <span className="inline-flex items-center gap-2">
                        <BriefcaseBusiness className="h-4 w-4 text-slate-400" />
                        {employee.role}
                      </span>
                      <span className="hidden text-slate-300 sm:inline">•</span>
                      <span className="inline-flex items-center gap-2">
                        <UserRound className="h-4 w-4 text-slate-400" />
                        {employee.department}
                      </span>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <InfoPill icon={Mail} label="Email" value={employee.email} />
                    <InfoPill icon={Phone} label="Phone" value={employee.phone} />
                    <InfoPill icon={MapPin} label="Location" value={employee.location} />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button asChild variant="outline" className="border-slate-200 bg-white">
                <Link href={`/employees/${employee.id}/edit`}>
                  <Pencil className="h-4 w-4" />
                  Edit
                </Link>
              </Button>
              <Button variant="ghost" className="border border-blue-100 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:text-blue-800">
                <ShieldCheck className="h-4 w-4" />
                Mark reviewed
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <CardDescription className="text-sm font-medium text-slate-500">{stat.label}</CardDescription>
              <CardTitle className="text-3xl text-slate-950">{stat.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <Separator className="mb-3 bg-slate-100" />
              <p className="text-sm leading-6 text-slate-600">{stat.note}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <Tabs defaultValue="overview" className="space-y-6">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="p-4 sm:p-5">
            <TabsList className="w-full justify-start gap-2 overflow-x-auto border-slate-200 bg-slate-50">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="attendance">Attendance</TabsTrigger>
              <TabsTrigger value="leave">Leave</TabsTrigger>
              <TabsTrigger value="payroll">Payroll</TabsTrigger>
              <TabsTrigger value="documents">Documents</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
            </TabsList>
          </CardContent>
        </Card>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-4 xl:grid-cols-3">
            {overviewSections.map((section) => (
              <Card key={section.title} className="border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <CardTitle>{section.title}</CardTitle>
                  <CardDescription>{section.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {section.items.map((item, index) => (
                    <div key={item.label} className="space-y-4">
                      <div className="space-y-1">
                        <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">{item.label}</p>
                        <p className="text-sm font-medium text-slate-900">{item.value}</p>
                      </div>
                      {index < section.items.length - 1 ? <Separator className="bg-slate-100" /> : null}
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {secondaryTabs.map((tab) => {
          const Icon = tab.icon

          return (
            <TabsContent key={tab.value} value={tab.value} className="space-y-6">
              <Card className="border-slate-200 bg-white shadow-sm">
                <CardContent className="flex flex-col gap-4 p-6 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-slate-950">{tab.title}</h3>
                        <p className="text-sm text-slate-500">Focused employee insight</p>
                      </div>
                    </div>
                    <p className="max-w-3xl text-sm leading-6 text-slate-600">{tab.description}</p>
                  </div>
                  <Badge variant="outline" className="w-fit border-slate-200 bg-slate-50 text-slate-600">
                    {employee.id}
                  </Badge>
                </CardContent>
              </Card>
            </TabsContent>
          )
        })}
      </Tabs>
    </div>
  )
}

function InfoPill({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Mail
  label: string
  value: string
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-start gap-3">
        <div className="rounded-lg bg-white p-2 text-slate-600 shadow-sm">
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{label}</p>
          <p className="mt-1 truncate text-sm font-medium text-slate-900">{value}</p>
        </div>
      </div>
    </div>
  )
}
