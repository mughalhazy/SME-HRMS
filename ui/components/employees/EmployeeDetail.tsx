'use client'

import {
  Activity,
  BriefcaseBusiness,
  CalendarClock,
  FileText,
  Mail,
  MapPin,
  Pencil,
  Phone,
  ShieldAlert,
  Sparkles,
  Wallet,
} from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const stats = [
  {
    label: 'Attendance %',
    value: '96.4%',
    note: 'Present 21 of 22 working days',
  },
  {
    label: 'Leaves taken',
    value: '08',
    note: '3 casual · 5 annual',
  },
  {
    label: 'Salary band',
    value: 'B4',
    note: 'Senior IC compensation tier',
  },
  {
    label: 'Performance score',
    value: '4.7/5',
    note: 'Exceeded expectations this quarter',
  },
]

const overviewSections = [
  {
    title: 'Personal info',
    description: 'Core employee identity and profile details.',
    items: [
      { label: 'Full name', value: 'Ahmed Khan' },
      { label: 'Employee ID', value: 'EMP-1024' },
      { label: 'Date of birth', value: 'May 14, 1991' },
      { label: 'Nationality', value: 'Pakistani' },
      { label: 'Marital status', value: 'Married' },
    ],
  },
  {
    title: 'Job info',
    description: 'Current position, reporting line, and employment details.',
    items: [
      { label: 'Role', value: 'Senior Engineer' },
      { label: 'Department', value: 'Engineering' },
      { label: 'Manager', value: 'Fatima Noor' },
      { label: 'Employment type', value: 'Full-time' },
      { label: 'Joining date', value: 'January 10, 2021' },
    ],
  },
  {
    title: 'Contact info',
    description: 'Preferred channels and location data for employee outreach.',
    items: [
      { label: 'Work email', value: 'ahmed.khan@smehrms.com' },
      { label: 'Phone', value: '+1 (415) 555-0184' },
      { label: 'Location', value: 'San Francisco, CA' },
      { label: 'Address', value: '145 Market Street, Suite 900' },
      { label: 'Emergency contact', value: 'Sara Khan · +1 (415) 555-0172' },
    ],
  },
]

const secondaryTabs = [
  {
    value: 'attendance',
    title: 'Attendance summary',
    description: 'Consistent on-time presence with a strong punctuality trend over the last 90 days.',
    icon: CalendarClock,
  },
  {
    value: 'leave',
    title: 'Leave balance',
    description: '12 annual leave days and 4 sick leave days remain available for the current cycle.',
    icon: Sparkles,
  },
  {
    value: 'payroll',
    title: 'Payroll snapshot',
    description: 'Monthly payroll processed on time with no pending adjustments or reimbursement issues.',
    icon: Wallet,
  },
  {
    value: 'documents',
    title: 'Document center',
    description: 'Contract, national ID, and performance letters are uploaded and verified by HR operations.',
    icon: FileText,
  },
  {
    value: 'activity',
    title: 'Recent activity',
    description: 'Latest employee events include review completion, attendance regularization, and profile updates.',
    icon: Activity,
  },
]

export function EmployeeDetail() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
      <Card className="border-slate-200 bg-white shadow-sm">
        <CardContent className="p-6 lg:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
              <Avatar className="h-20 w-20 border-slate-200 bg-slate-50">
                <AvatarFallback className="bg-slate-100 text-xl font-semibold text-slate-700">AK</AvatarFallback>
              </Avatar>

              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Ahmed Khan</h2>
                    <Badge variant="success">Active</Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
                    <span className="inline-flex items-center gap-2">
                      <BriefcaseBusiness className="h-4 w-4 text-slate-400" />
                      Senior Engineer
                    </span>
                    <span className="hidden text-slate-300 sm:inline">•</span>
                    <span className="inline-flex items-center gap-2">
                      <ShieldAlert className="h-4 w-4 text-slate-400" />
                      Engineering Department
                    </span>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <InfoPill icon={Mail} label="Email" value="ahmed.khan@smehrms.com" />
                  <InfoPill icon={Phone} label="Phone" value="+1 (415) 555-0184" />
                  <InfoPill icon={MapPin} label="Location" value="San Francisco, CA" />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button variant="outline" className="border-slate-200 bg-white">
                <Pencil className="h-4 w-4" />
                Edit
              </Button>
              <Button variant="ghost" className="border border-rose-100 bg-rose-50 text-rose-700 hover:bg-rose-100 hover:text-rose-800">
                <ShieldAlert className="h-4 w-4" />
                Deactivate
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

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

      <Tabs defaultValue="overview" className="gap-5">
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

        <TabsContent value="overview">
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
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1">
                          <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">{item.label}</p>
                          <p className="text-sm font-medium text-slate-900">{item.value}</p>
                        </div>
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
            <TabsContent key={tab.value} value={tab.value}>
              <Card className="border-slate-200 bg-white shadow-sm">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-slate-600">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>{tab.title}</CardTitle>
                      <CardDescription>{tab.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm leading-6 text-slate-600">
                    This tab is ready for deeper employee-specific content while keeping the current detail page clean, light, and easy to scan.
                  </div>
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
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">{label}</p>
      <p className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
        <Icon className="h-4 w-4 text-slate-400" />
        {value}
      </p>
    </div>
  )
}
