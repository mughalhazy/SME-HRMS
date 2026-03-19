import {
  Bell,
  BriefcaseBusiness,
  Building2,
  CalendarCheck2,
  ChevronRight,
  Clock3,
  LayoutGrid,
  Search,
  Settings,
  Users,
  Wallet,
} from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

type NavItem = {
  label: string
  icon: typeof LayoutGrid
  active?: boolean
}

type Metric = {
  label: string
  value: string
  detail: string
}

type AlertItem = {
  title: string
  meta: string
  badge: string
}

type ActivityItem = {
  title: string
  detail: string
  time: string
}

const navigationItems: NavItem[] = [
  { label: 'Employees', icon: Users, active: true },
  { label: 'Attendance', icon: CalendarCheck2 },
  { label: 'Leave', icon: BriefcaseBusiness },
  { label: 'Payroll', icon: Wallet },
  { label: 'Departments', icon: Building2 },
  { label: 'Settings', icon: Settings },
]

const metrics: Metric[] = [
  { label: 'Total Employees', value: '1248', detail: '+24 this month' },
  { label: 'Present Today', value: '1103', detail: '88.4% attendance rate' },
  { label: 'On Leave', value: '42', detail: '6 returning tomorrow' },
  { label: 'Pending Approvals', value: '18', detail: '7 urgent requests' },
]

const attendanceBars = [64, 82, 74, 90, 76, 95, 84]

const departmentDistribution = [
  { name: 'Operations', value: 32, tone: 'bg-slate-900' },
  { name: 'Engineering', value: 24, tone: 'bg-slate-700' },
  { name: 'Sales', value: 18, tone: 'bg-slate-500' },
  { name: 'HR', value: 14, tone: 'bg-slate-400' },
  { name: 'Finance', value: 12, tone: 'bg-slate-300' },
]

const alerts: AlertItem[] = [
  { title: 'Late employees', meta: '12 check-ins after 9:15 AM', badge: 'Needs follow-up' },
  { title: 'Pending approvals', meta: '18 leave and attendance actions', badge: 'Action required' },
]

const activities: ActivityItem[] = [
  { title: 'New hires onboarded', detail: 'Ava Patel and Marcus Lee joined the Product team.', time: '10 min ago' },
  { title: 'Leave requests submitted', detail: '5 leave requests are waiting for manager review.', time: '32 min ago' },
  { title: 'Payroll processed', detail: 'March semi-monthly payroll was finalized for 1,248 employees.', time: '1 hour ago' },
]

export function Dashboard() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white xl:border-b-0 xl:border-r">
          <div className="flex h-full flex-col gap-6 p-6">
            <div className="space-y-3">
              <Badge className="w-fit bg-slate-100 text-slate-700">HRMS Dashboard</Badge>
              <div>
                <h1 className="text-xl font-semibold tracking-tight text-slate-950">People Operations</h1>
                <p className="mt-1 text-sm leading-6 text-slate-500">A light workspace for daily workforce monitoring and approvals.</p>
              </div>
            </div>

            <Separator />

            <nav aria-label="Sidebar navigation" className="space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon

                return (
                  <button
                    key={item.label}
                    className={cn(
                      'flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition-colors',
                      item.active
                        ? 'border-slate-200 bg-slate-100 text-slate-950'
                        : 'border-transparent bg-white text-slate-500 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-950',
                    )}
                    type="button"
                  >
                    <span className="flex items-center gap-3">
                      <span className={cn('rounded-xl p-2', item.active ? 'bg-white text-slate-900 shadow-sm' : 'bg-slate-100 text-slate-500')}>
                        <Icon className="h-4 w-4" />
                      </span>
                      <span className="text-sm font-medium">{item.label}</span>
                    </span>
                    <ChevronRight className="h-4 w-4 text-slate-400" />
                  </button>
                )
              })}
            </nav>

            <div className="mt-auto rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">Daily snapshot</p>
              <p className="mt-1 text-sm leading-6 text-slate-500">Attendance is trending above weekly average and approvals are within SLA.</p>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-col">
          <header className="border-b border-slate-200 bg-white">
            <div className="flex flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Dashboard overview</p>
                <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">HRMS command center</h2>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative min-w-[280px]">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input className="border-slate-200 bg-slate-50 pl-9" placeholder="Search employees, departments, or requests" />
                </div>
                <div className="flex items-center gap-3">
                  <Button className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50" size="icon" variant="outline">
                    <Bell className="h-4 w-4" />
                  </Button>
                  <div className="flex items-center gap-3 rounded-full border border-slate-200 bg-slate-50 px-3 py-2">
                    <Avatar className="h-10 w-10 border-slate-200">
                      <AvatarFallback>HR</AvatarFallback>
                    </Avatar>
                    <div className="hidden text-left sm:block">
                      <p className="text-sm font-semibold text-slate-900">Hannah Reed</p>
                      <p className="text-xs text-slate-500">HR Manager</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 p-6 lg:p-8">
            <div className="space-y-6">
              <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {metrics.map((metric) => (
                  <Card key={metric.label} className="border-slate-200 bg-white shadow-sm">
                    <CardHeader className="pb-2">
                      <p className="text-sm font-medium text-slate-500">{metric.label}</p>
                      <CardTitle className="text-3xl font-semibold text-slate-950">{metric.value}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Badge className="bg-slate-100 text-slate-600">{metric.detail}</Badge>
                    </CardContent>
                  </Card>
                ))}
              </section>

              <section className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,1fr)]">
                <Card className="border-slate-200 bg-white shadow-sm">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <CardTitle>Attendance trend</CardTitle>
                        <p className="mt-1 text-sm text-slate-500">Placeholder chart for daily attendance over the last 7 days.</p>
                      </div>
                      <Badge className="bg-emerald-50 text-emerald-700">+3.2% vs last week</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex h-72 items-end gap-4 rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-6">
                      {attendanceBars.map((bar, index) => (
                        <div key={bar} className="flex flex-1 flex-col items-center justify-end gap-3">
                          <div className="w-full rounded-t-2xl bg-slate-900/90" style={{ height: `${bar * 2}px` }} />
                          <span className="text-xs font-medium text-slate-400">D{index + 1}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-slate-200 bg-white shadow-sm">
                  <CardHeader className="pb-4">
                    <CardTitle>Department distribution</CardTitle>
                    <p className="text-sm text-slate-500">Placeholder split of headcount across departments.</p>
                  </CardHeader>
                  <CardContent className="space-y-5">
                    <div className="flex h-72 items-center justify-center rounded-full border border-dashed border-slate-200 bg-slate-50 p-8">
                      <div className="grid h-52 w-52 place-items-center rounded-full border-[18px] border-slate-300 border-t-slate-900 border-r-slate-700 border-b-slate-500 bg-white text-center">
                        <div>
                          <p className="text-sm text-slate-500">Largest team</p>
                          <p className="text-lg font-semibold text-slate-950">Operations</p>
                          <p className="text-xs text-slate-400">32% of workforce</p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {departmentDistribution.map((department) => (
                        <div key={department.name} className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <span className={cn('h-3 w-3 rounded-full', department.tone)} />
                            <span className="text-sm font-medium text-slate-600">{department.name}</span>
                          </div>
                          <span className="text-sm text-slate-400">{department.value}%</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </section>

              <section className="grid gap-6 xl:grid-cols-[minmax(320px,0.9fr)_minmax(0,1.1fr)]">
                <Card className="border-slate-200 bg-white shadow-sm">
                  <CardHeader className="pb-4">
                    <CardTitle>Alerts panel</CardTitle>
                    <p className="text-sm text-slate-500">Review the highest priority employee and approval issues.</p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {alerts.map((alert, index) => (
                      <div key={alert.title} className="space-y-4">
                        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold text-slate-900">{alert.title}</p>
                              <p className="mt-1 text-sm text-slate-500">{alert.meta}</p>
                            </div>
                            <Badge className="bg-amber-50 text-amber-700">{alert.badge}</Badge>
                          </div>
                        </div>
                        {index < alerts.length - 1 ? <Separator /> : null}
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className="border-slate-200 bg-white shadow-sm">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <CardTitle>Activity feed</CardTitle>
                        <p className="text-sm text-slate-500">Recent actions from hiring, leave, and payroll workflows.</p>
                      </div>
                      <Button className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50" variant="outline">View all</Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {activities.map((activity, index) => (
                      <div key={activity.title} className="space-y-4">
                        <div className="flex gap-4">
                          <div className="flex flex-col items-center">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-700">
                              <Clock3 className="h-4 w-4" />
                            </div>
                            {index < activities.length - 1 ? <Separator className="mt-3 h-12" orientation="vertical" /> : null}
                          </div>
                          <div className="flex-1 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <p className="text-sm font-semibold text-slate-900">{activity.title}</p>
                              <span className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">{activity.time}</span>
                            </div>
                            <p className="mt-2 text-sm leading-6 text-slate-500">{activity.detail}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </section>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
