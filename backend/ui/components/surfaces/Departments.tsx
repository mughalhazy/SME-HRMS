import { ArrowRight, Building2, GitBranch, Plus, SearchCheck, Users } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/base/avatar'
import { Badge } from '@/components/base/badge'
import { Button } from '@/components/base/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/base/card'
import { KpiGrid, StatCard } from '@/components/base/page'
import { Separator } from '@/components/base/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/base/table'

type KpiCard = {
  title: string
  value: string
  note: string
  icon: typeof Building2
}

type DepartmentRecord = {
  name: string
  head: string
  headInitials: string
  employees: number
  openRoles: number
  status: 'Scaling' | 'Stable' | 'Hiring'
  focus: string
}

type OrgNode = {
  team: string
  manager: string
  reports: string[]
}

const kpiCards: KpiCard[] = [
  {
    title: 'Total Departments',
    value: '12',
    note: 'Cross-functional business units',
    icon: Building2,
  },
  {
    title: 'Total Employees',
    value: '1,248',
    note: 'Company-wide active workforce',
    icon: Users,
  },
  {
    title: 'Open Positions',
    value: '34',
    note: 'Priority roles awaiting hires',
    icon: SearchCheck,
  },
  {
    title: 'Avg Team Size',
    value: '104',
    note: 'Average headcount per department',
    icon: GitBranch,
  },
]

const departments: DepartmentRecord[] = [
  {
    name: 'Engineering',
    head: 'Maya Chen',
    headInitials: 'MC',
    employees: 286,
    openRoles: 12,
    status: 'Scaling',
    focus: 'Platform modernization and product delivery',
  },
  {
    name: 'Human Resources',
    head: 'Jordan Ellis',
    headInitials: 'JE',
    employees: 64,
    openRoles: 2,
    status: 'Stable',
    focus: 'People operations, onboarding, and retention',
  },
  {
    name: 'Finance',
    head: 'Avery Brooks',
    headInitials: 'AB',
    employees: 49,
    openRoles: 1,
    status: 'Stable',
    focus: 'Financial planning, controls, and reporting',
  },
  {
    name: 'Sales',
    head: 'Priya Nair',
    headInitials: 'PN',
    employees: 198,
    openRoles: 8,
    status: 'Hiring',
    focus: 'Regional growth and enterprise pipeline expansion',
  },
  {
    name: 'Customer Success',
    head: 'Daniel Ortiz',
    headInitials: 'DO',
    employees: 154,
    openRoles: 4,
    status: 'Scaling',
    focus: 'Retention, renewals, and service excellence',
  },
  {
    name: 'Marketing',
    head: 'Sofia Bennett',
    headInitials: 'SB',
    employees: 103,
    openRoles: 3,
    status: 'Hiring',
    focus: 'Brand campaigns and demand generation',
  },
]

const orgStructure: OrgNode[] = [
  {
    team: 'Executive Operations',
    manager: 'CEO · Olivia Parker',
    reports: ['VP People · Jordan Ellis', 'VP Finance · Avery Brooks', 'VP Operations · Mateo Clark'],
  },
  {
    team: 'Product & Delivery',
    manager: 'CTO · Maya Chen',
    reports: ['Engineering Managers · 8 teams', 'Design Lead · Experience Studio', 'QA Lead · Release Excellence'],
  },
  {
    team: 'Revenue Organization',
    manager: 'CRO · Priya Nair',
    reports: ['Regional Sales Directors · North America', 'Growth Marketing · Demand Center', 'Customer Success Lead · Enterprise Accounts'],
  },
]

function getStatusVariant(status: DepartmentRecord['status']) {
  switch (status) {
    case 'Stable':
      return 'outline'
    case 'Hiring':
      return 'default'
    case 'Scaling':
      return 'success'
    default:
      return 'outline'
  }
}

export function Departments() {
  return (
    <div className="flex flex-col gap-6 text-slate-950">
      <Card className="bg-white shadow-sm">
        <CardHeader className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <Badge variant="outline" className="w-fit bg-slate-50">Department Workspace</Badge>
            <div>
              <CardTitle className="text-3xl">Departments</CardTitle>
              <CardDescription>
                View organizational coverage, leadership ownership, and team health in a single balanced workspace.
              </CardDescription>
            </div>
          </div>
          <Button className="w-full sm:w-auto">
            <Plus className="h-4 w-4" />
            Add Department
          </Button>
        </CardHeader>
      </Card>

      <KpiGrid>
        {kpiCards.map((card) => {
          const Icon = card.icon

          return (
            <StatCard key={card.title} title={card.title} value={card.value} hint={card.note} icon={Icon} className="bg-white shadow-sm" />
          )
        })}
      </KpiGrid>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,0.95fr)]">
        <Card className="overflow-hidden bg-white shadow-sm">
          <CardHeader className="space-y-2">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-xl">Departments Table</CardTitle>
                <CardDescription>Leadership, active staffing, open hiring demand, and operational status.</CardDescription>
              </div>
              <Badge className="w-fit">12 Departments</Badge>
            </div>
          </CardHeader>
          <CardContent className="px-0 pb-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Department Name</TableHead>
                  <TableHead>Head</TableHead>
                  <TableHead>Employees count</TableHead>
                  <TableHead>Open roles</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {departments.map((department) => (
                  <TableRow key={department.name}>
                    <TableCell>
                      <div className="space-y-1">
                        <p className="font-medium text-slate-950">{department.name}</p>
                        <p className="text-sm text-slate-500">{department.focus}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9 border-slate-200 bg-white">
                          <AvatarFallback>{department.headInitials}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium text-slate-950">{department.head}</p>
                          <p className="text-sm text-slate-500">Department Head</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-medium text-slate-700">{department.employees}</TableCell>
                    <TableCell className="text-slate-700">{department.openRoles}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(department.status)}>{department.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" size="sm">View</Button>
                        <Button size="sm">Manage</Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="text-xl">Org Structure</CardTitle>
            <CardDescription>Simple hierarchy placeholder showing manager-to-team relationships.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {orgStructure.map((node, index) => (
              <div key={node.team} className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
                    <GitBranch className="h-4 w-4" />
                    {node.team}
                  </div>
                  <div className="mt-3 rounded-xl border border-slate-200 bg-white p-4">
                    <p className="text-sm text-slate-500">Manager</p>
                    <p className="mt-1 font-semibold text-slate-950">{node.manager}</p>
                  </div>
                  <div className="mt-4 space-y-3 pl-4">
                    {node.reports.map((report) => (
                      <div key={report} className="relative rounded-xl border border-dashed border-slate-200 bg-white px-4 py-3 before:absolute before:-left-4 before:top-1/2 before:h-px before:w-4 before:bg-slate-300 before:content-['']">
                        <p className="text-sm font-medium text-slate-700">{report}</p>
                      </div>
                    ))}
                  </div>
                </div>
                {index < orgStructure.length - 1 ? <Separator /> : null}
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <Card className="bg-white shadow-sm">
        <CardHeader className="space-y-2">
          <CardTitle className="text-xl">Department Cards</CardTitle>
          <CardDescription>Secondary visual summary for quick scanning across leadership teams.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {departments.map((department) => (
              <div key={department.name} className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <p className="text-lg font-semibold text-slate-950">{department.name}</p>
                    <p className="text-sm text-slate-500">{department.focus}</p>
                  </div>
                  <Badge variant={getStatusVariant(department.status)}>{department.status}</Badge>
                </div>
                <Separator className="my-4" />
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10 border-slate-200 bg-white">
                    <AvatarFallback>{department.headInitials}</AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium text-slate-950">{department.head}</p>
                    <p className="text-sm text-slate-500">Head of {department.name}</p>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-white bg-white p-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Employees</p>
                    <p className="mt-1 text-xl font-semibold text-slate-950">{department.employees}</p>
                  </div>
                  <div className="rounded-xl border border-white bg-white p-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Open roles</p>
                    <p className="mt-1 text-xl font-semibold text-slate-950">{department.openRoles}</p>
                  </div>
                </div>
                <Button variant="outline" className="mt-4 w-full justify-between">
                  View department details
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
