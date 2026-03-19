'use client'

import { useMemo, useState } from 'react'
import {
  CalendarDays,
  CalendarRange,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Ellipsis,
  Search,
  UserCheck,
  XCircle,
} from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input, Select } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

type LeaveStatus = 'Pending' | 'Approved' | 'Rejected'

type LeaveRequest = {
  id: string
  employee: string
  initials: string
  leaveType: 'Annual Leave' | 'Sick Leave' | 'Casual Leave' | 'Work From Home'
  fromDate: string
  toDate: string
  days: number
  status: LeaveStatus
  manager: string
  department: string
}

const leaveRequests: LeaveRequest[] = [
  {
    id: 'LR-1042',
    employee: 'Ava Thompson',
    initials: 'AT',
    leaveType: 'Annual Leave',
    fromDate: '2026-03-22',
    toDate: '2026-03-26',
    days: 5,
    status: 'Pending',
    manager: 'Sophia Patel',
    department: 'Operations',
  },
  {
    id: 'LR-1043',
    employee: 'Noah Kim',
    initials: 'NK',
    leaveType: 'Sick Leave',
    fromDate: '2026-03-20',
    toDate: '2026-03-21',
    days: 2,
    status: 'Pending',
    manager: 'Daniel Reed',
    department: 'Engineering',
  },
  {
    id: 'LR-1044',
    employee: 'Emma Garcia',
    initials: 'EG',
    leaveType: 'Casual Leave',
    fromDate: '2026-03-25',
    toDate: '2026-03-25',
    days: 1,
    status: 'Approved',
    manager: 'Sophia Patel',
    department: 'Finance',
  },
  {
    id: 'LR-1045',
    employee: 'Liam Johnson',
    initials: 'LJ',
    leaveType: 'Annual Leave',
    fromDate: '2026-03-29',
    toDate: '2026-04-02',
    days: 5,
    status: 'Approved',
    manager: 'Priya Nair',
    department: 'People Ops',
  },
  {
    id: 'LR-1046',
    employee: 'Olivia Chen',
    initials: 'OC',
    leaveType: 'Work From Home',
    fromDate: '2026-03-23',
    toDate: '2026-03-23',
    days: 1,
    status: 'Rejected',
    manager: 'Daniel Reed',
    department: 'Design',
  },
  {
    id: 'LR-1047',
    employee: 'Mason Brown',
    initials: 'MB',
    leaveType: 'Annual Leave',
    fromDate: '2026-04-05',
    toDate: '2026-04-09',
    days: 5,
    status: 'Pending',
    manager: 'Sophia Patel',
    department: 'Sales',
  },
]

const kpis = [
  { label: 'Pending Approvals', value: '18', icon: Clock3, tone: 'text-amber-600 bg-amber-50 border-amber-200' },
  { label: 'Approved This Month', value: '64', icon: CheckCircle2, tone: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
  { label: 'Rejected', value: '9', icon: XCircle, tone: 'text-rose-600 bg-rose-50 border-rose-200' },
  { label: 'On Leave Today', value: '42', icon: UserCheck, tone: 'text-blue-600 bg-blue-50 border-blue-200' },
] as const

const balanceSummary = [
  { label: 'Annual', used: 12, remaining: 8, color: 'bg-blue-500' },
  { label: 'Sick', used: 3, remaining: 7, color: 'bg-emerald-500' },
  { label: 'Casual', used: 2, remaining: 4, color: 'bg-amber-500' },
]

const calendarEvents = [
  { date: '2026-03-22', label: 'Ava Thompson leave starts' },
  { date: '2026-03-25', label: 'Emma Garcia casual leave' },
  { date: '2026-03-29', label: 'Liam Johnson leave begins' },
  { date: '2026-04-05', label: 'Mason Brown annual leave' },
]

const statusVariant: Record<LeaveStatus, 'default' | 'success' | 'outline'> = {
  Pending: 'default',
  Approved: 'success',
  Rejected: 'outline',
}

const statusClassName: Record<LeaveStatus, string> = {
  Pending: 'bg-amber-50 text-amber-700 border-amber-200',
  Approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Rejected: 'bg-rose-50 text-rose-700 border-rose-200',
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatRange(start: string, end: string) {
  return `${formatDate(start)} - ${formatDate(end)}`
}

export function LeaveManagement() {
  const [searchTerm, setSearchTerm] = useState('')
  const [leaveType, setLeaveType] = useState('All types')
  const [status, setStatus] = useState('All statuses')
  const [selectedRequestId, setSelectedRequestId] = useState('LR-1042')
  const [selectedDate, setSelectedDate] = useState(new Date('2026-03-22T00:00:00'))

  const filteredRequests = useMemo(() => {
    return leaveRequests.filter((request) => {
      const matchesSearch =
        searchTerm.trim().length === 0 ||
        request.employee.toLowerCase().includes(searchTerm.toLowerCase()) ||
        request.manager.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesType = leaveType === 'All types' || request.leaveType === leaveType
      const matchesStatus = status === 'All statuses' || request.status === status

      return matchesSearch && matchesType && matchesStatus
    })
  }, [leaveType, searchTerm, status])

  const selectedRequest =
    filteredRequests.find((request) => request.id === selectedRequestId) ??
    leaveRequests.find((request) => request.id === selectedRequestId) ??
    leaveRequests[0]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 rounded-[var(--radius-surface)] border border-[var(--border)] bg-white p-6 shadow-[var(--shadow-surface)] lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Time off operations</p>
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Leave Management</h1>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Review requests, prioritize pending approvals, and keep employee leave balances visible in one clean workspace.
            </p>
          </div>
        </div>

        <Button className="w-full lg:w-auto">
          Request Leave
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpis.map((item) => {
          const Icon = item.icon

          return (
            <Card key={item.label} className={cn('border', item.label === 'Pending Approvals' && 'ring-2 ring-amber-200/70')}>
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-sm font-medium text-slate-500">{item.label}</p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{item.value}</p>
                </div>
                <div className={cn('rounded-2xl border p-3', item.tone)}>
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="grid gap-3 xl:grid-cols-[minmax(0,1.4fr)_220px_220px_220px]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                className="pl-9"
                placeholder="Search employee or manager"
              />
            </div>

            <Select value={leaveType} onChange={(event) => setLeaveType(event.target.value)}>
              <option>All types</option>
              <option>Annual Leave</option>
              <option>Sick Leave</option>
              <option>Casual Leave</option>
              <option>Work From Home</option>
            </Select>

            <Select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option>All statuses</option>
              <option>Pending</option>
              <option>Approved</option>
              <option>Rejected</option>
            </Select>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="justify-between">
                  <span className="inline-flex items-center gap-2">
                    <CalendarRange className="h-4 w-4" />
                    {formatRange('2026-03-19', '2026-03-31')}
                  </span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-[22rem] p-3">
                <div className="mb-3">
                  <p className="text-sm font-semibold text-slate-950">Date range picker</p>
                  <p className="text-xs text-slate-500">Use the calendar to focus on upcoming approvals.</p>
                </div>
                <Calendar month={new Date('2026-03-01T00:00:00')} selected={selectedDate} onSelect={(date) => setSelectedDate(date)} events={calendarEvents} />
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 2xl:grid-cols-[minmax(0,1.8fr)_360px]">
        <Card className="overflow-hidden">
          <CardHeader className="border-b border-[var(--border)] bg-slate-50/80">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>Leave Requests</CardTitle>
                <CardDescription>Pending requests are highlighted to keep the approval queue easy to scan.</CardDescription>
              </div>
              <Badge className="w-fit bg-amber-50 text-amber-700">{filteredRequests.filter((request) => request.status === 'Pending').length} pending</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Leave type</TableHead>
                  <TableHead>From date</TableHead>
                  <TableHead>To date</TableHead>
                  <TableHead>Days</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Manager</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRequests.map((request) => (
                  <TableRow
                    key={request.id}
                    className={cn(
                      'cursor-pointer',
                      request.status === 'Pending' && 'bg-amber-50/60 hover:bg-amber-50',
                      selectedRequest?.id === request.id && 'ring-1 ring-inset ring-blue-200',
                    )}
                    onClick={() => setSelectedRequestId(request.id)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback>{request.initials}</AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium text-slate-950">{request.employee}</div>
                          <div className="text-xs text-slate-500">{request.department}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-medium text-slate-700">{request.leaveType}</TableCell>
                    <TableCell className="text-slate-600">{formatDate(request.fromDate)}</TableCell>
                    <TableCell className="text-slate-600">{formatDate(request.toDate)}</TableCell>
                    <TableCell className="text-slate-600">{request.days}</TableCell>
                    <TableCell>
                      <Badge variant={statusVariant[request.status]} className={statusClassName[request.status]}>
                        {request.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-600">{request.manager}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {request.status === 'Pending' ? (
                          <>
                            <Button size="sm" className="h-8">Approve</Button>
                            <Button size="sm" variant="outline" className="h-8 border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700">
                              Reject
                            </Button>
                          </>
                        ) : null}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button size="icon" variant="ghost" className="h-8 w-8" onClick={(event) => event.stopPropagation()}>
                              <Ellipsis className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={(event) => event.stopPropagation()}>Approve</DropdownMenuItem>
                            <DropdownMenuItem onClick={(event) => event.stopPropagation()}>Reject</DropdownMenuItem>
                            <DropdownMenuItem onClick={(event) => event.stopPropagation()}>View</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Leave balance summary</CardTitle>
              <CardDescription>Selected employee: {selectedRequest.employee}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 rounded-2xl border border-[var(--border)] bg-slate-50 p-4">
                <Avatar className="h-12 w-12">
                  <AvatarFallback>{selectedRequest.initials}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-slate-950">{selectedRequest.employee}</p>
                  <p className="text-sm text-slate-500">Reporting to {selectedRequest.manager}</p>
                </div>
              </div>

              {balanceSummary.map((item) => {
                const total = item.used + item.remaining
                const width = `${(item.used / total) * 100}%`

                return (
                  <div key={item.label} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-700">{item.label}</span>
                      <span className="text-slate-500">{item.remaining} days remaining</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                      <div className={cn('h-full rounded-full', item.color)} style={{ width }} />
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{item.used} used</span>
                      <span>{total} allocated</span>
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle>Upcoming leaves calendar</CardTitle>
                  <CardDescription>Simple placeholder to preview planned time off.</CardDescription>
                </div>
                <Badge variant="outline" className="gap-1">
                  <CalendarDays className="h-3.5 w-3.5" />
                  Placeholder
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Calendar month={new Date('2026-03-01T00:00:00')} selected={selectedDate} onSelect={(date) => setSelectedDate(date)} events={calendarEvents} />
              <div className="space-y-2 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4">
                {calendarEvents.slice(0, 3).map((event) => (
                  <div key={event.date} className="flex items-start justify-between gap-3 text-sm">
                    <div>
                      <p className="font-medium text-slate-700">{event.label}</p>
                      <p className="text-slate-500">{formatDate(event.date)}</p>
                    </div>
                    <Badge variant="outline">Upcoming</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
