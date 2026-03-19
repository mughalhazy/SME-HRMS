'use client'

import { useMemo, useState } from 'react'
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ChevronsUpDown,
  Clock3,
  Download,
  Eye,
  MoreHorizontal,
  TimerReset,
  TriangleAlert,
  UserRoundX,
} from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input, Select } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

type AttendanceStatus = 'Present' | 'Late' | 'Absent' | 'Leave'

type AttendanceRow = {
  id: string
  name: string
  employeeId: string
  department: string
  checkIn: string
  checkOut: string
  status: AttendanceStatus
  workHours: string
}

type CalendarProps = {
  selectedDate: Date
  month: Date
  onMonthChange: (date: Date) => void
  onSelectDate: (date: Date) => void
}

const attendanceRows: AttendanceRow[] = [
  { id: '1', name: 'Ariana Flores', employeeId: 'EMP-1042', department: 'Operations', checkIn: '08:54 AM', checkOut: '05:31 PM', status: 'Present', workHours: '8h 37m' },
  { id: '2', name: 'Darnell Price', employeeId: 'EMP-1188', department: 'Finance', checkIn: '09:17 AM', checkOut: '06:04 PM', status: 'Late', workHours: '8h 47m' },
  { id: '3', name: 'Mei Nakamura', employeeId: 'EMP-0964', department: 'Engineering', checkIn: '08:41 AM', checkOut: '05:45 PM', status: 'Present', workHours: '9h 04m' },
  { id: '4', name: 'Jamal Carter', employeeId: 'EMP-1215', department: 'Customer Success', checkIn: '--', checkOut: '--', status: 'Absent', workHours: '0h 00m' },
  { id: '5', name: 'Nina Patel', employeeId: 'EMP-0871', department: 'Human Resources', checkIn: '--', checkOut: '--', status: 'Leave', workHours: '0h 00m' },
  { id: '6', name: 'Carlos Mendes', employeeId: 'EMP-1130', department: 'Operations', checkIn: '09:11 AM', checkOut: '—', status: 'Late', workHours: '7h 26m' },
  { id: '7', name: 'Elena Petrova', employeeId: 'EMP-1029', department: 'Engineering', checkIn: '08:48 AM', checkOut: '05:40 PM', status: 'Present', workHours: '8h 52m' },
  { id: '8', name: 'Marcus Lee', employeeId: 'EMP-1106', department: 'Sales', checkIn: '08:59 AM', checkOut: '—', status: 'Present', workHours: '7h 58m' },
]

const departments = ['All departments', 'Operations', 'Finance', 'Engineering', 'Customer Success', 'Human Resources', 'Sales']
const statuses = ['All statuses', 'Present', 'Late', 'Absent', 'Leave']
const dayNames = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

const kpis = [
  { label: 'Present Today', value: '1103', icon: Clock3, accent: 'text-emerald-600', bg: 'bg-emerald-50' },
  { label: 'Late', value: '76', icon: TriangleAlert, accent: 'text-amber-600', bg: 'bg-amber-50' },
  { label: 'On Leave', value: '42', icon: TimerReset, accent: 'text-sky-600', bg: 'bg-sky-50' },
  { label: 'Absent', value: '27', icon: UserRoundX, accent: 'text-rose-600', bg: 'bg-rose-50' },
] as const

const lateArrivals = [
  { name: 'Darnell Price', time: '09:17 AM', department: 'Finance' },
  { name: 'Carlos Mendes', time: '09:11 AM', department: 'Operations' },
  { name: 'Priya Raman', time: '09:09 AM', department: 'Sales' },
  { name: 'Brianna Cole', time: '09:06 AM', department: 'Engineering' },
]

const missingCheckouts = [
  { name: 'Carlos Mendes', since: 'Checked in 09:11 AM' },
  { name: 'Marcus Lee', since: 'Checked in 08:59 AM' },
  { name: 'Leah Kim', since: 'Checked in 08:51 AM' },
]

function getMonthDays(viewDate: Date) {
  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()
  const firstDay = new Date(year, month, 1)
  const startOffset = firstDay.getDay()

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(year, month, index - startOffset + 1)

    return {
      date,
      inMonth: date.getMonth() === month,
    }
  })
}

function formatFullDate(date: Date) {
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

function formatShortDate(date: Date) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

function getStatusBadgeVariant(status: AttendanceStatus) {
  switch (status) {
    case 'Present':
      return 'success' as const
    case 'Late':
      return 'outline' as const
    case 'Absent':
      return 'outline' as const
    case 'Leave':
      return 'default' as const
  }
}

function getStatusBadgeClassName(status: AttendanceStatus) {
  switch (status) {
    case 'Late':
      return 'border-amber-200 bg-amber-50 text-amber-700'
    case 'Absent':
      return 'border-rose-200 bg-rose-50 text-rose-700'
    case 'Leave':
      return 'bg-sky-100 text-sky-700'
    default:
      return ''
  }
}

function getInitials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function Calendar({ selectedDate, month, onMonthChange, onSelectDate }: CalendarProps) {
  const monthDays = useMemo(() => getMonthDays(month), [month])

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Date picker</p>
          <p className="mt-1 text-sm font-medium text-slate-600">{formatShortDate(selectedDate)}</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500">
          <CalendarDays className="h-4 w-4" />
        </div>
      </div>

      <div className="mb-3 flex items-center justify-between">
        <Button
          className="h-8 w-8 rounded-full"
          size="icon"
          type="button"
          variant="ghost"
          onClick={() => onMonthChange(new Date(month.getFullYear(), month.getMonth() - 1, 1))}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <p className="text-sm font-semibold text-slate-700">{month.toLocaleString('en-US', { month: 'long', year: 'numeric' })}</p>
        <Button
          className="h-8 w-8 rounded-full"
          size="icon"
          type="button"
          variant="ghost"
          onClick={() => onMonthChange(new Date(month.getFullYear(), month.getMonth() + 1, 1))}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center text-xs text-slate-400">
        {dayNames.map((day) => (
          <span key={day} className="py-1 font-medium">
            {day}
          </span>
        ))}
      </div>

      <div className="mt-1 grid grid-cols-7 gap-1">
        {monthDays.map(({ date, inMonth }) => {
          const isSelected = date.toDateString() === selectedDate.toDateString()
          const isToday = date.toDateString() === new Date('2026-03-19T00:00:00').toDateString()

          return (
            <button
              key={date.toISOString()}
              className={cn(
                'flex h-9 items-center justify-center rounded-lg text-sm transition-colors',
                inMonth ? 'text-slate-700 hover:bg-slate-100' : 'text-slate-300',
                isToday && !isSelected && 'font-semibold text-slate-950',
                isSelected && 'bg-slate-900 font-semibold text-white hover:bg-slate-900',
              )}
              type="button"
              onClick={() => {
                onSelectDate(date)
                onMonthChange(new Date(date.getFullYear(), date.getMonth(), 1))
              }}
            >
              {date.getDate()}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function Attendance() {
  const [selectedDate, setSelectedDate] = useState(() => new Date('2026-03-19T00:00:00'))
  const [calendarMonth, setCalendarMonth] = useState(() => new Date('2026-03-01T00:00:00'))
  const [department, setDepartment] = useState('All departments')
  const [status, setStatus] = useState('All statuses')
  const [search, setSearch] = useState('')

  const filteredRows = useMemo(() => {
    return attendanceRows.filter((row) => {
      const matchesDepartment = department === 'All departments' || row.department === department
      const matchesStatus = status === 'All statuses' || row.status === status
      const matchesSearch =
        search.trim().length === 0 ||
        row.name.toLowerCase().includes(search.toLowerCase()) ||
        row.employeeId.toLowerCase().includes(search.toLowerCase())

      return matchesDepartment && matchesStatus && matchesSearch
    })
  }, [department, search, status])

  return (
    <div className="min-h-full bg-[#f5f7fb] px-6 py-6 text-slate-900">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Attendance</h1>
          <p className="text-sm text-slate-500">Track daily workforce presence</p>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((item) => {
            const Icon = item.icon

            return (
              <Card key={item.label} className="border-slate-200 bg-white shadow-sm">
                <CardContent className="flex items-center justify-between p-5">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-slate-500">{item.label}</p>
                    <p className="text-3xl font-semibold tracking-tight text-slate-950">{item.value}</p>
                  </div>
                  <div className={cn('flex h-11 w-11 items-center justify-center rounded-xl border border-white/70', item.bg)}>
                    <Icon className={cn('h-5 w-5', item.accent)} />
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-6">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardContent className="grid gap-4 p-5 lg:grid-cols-2 xl:grid-cols-[280px_minmax(0,1fr)]">
                <Calendar
                  month={calendarMonth}
                  selectedDate={selectedDate}
                  onMonthChange={setCalendarMonth}
                  onSelectDate={setSelectedDate}
                />

                <div className="grid content-start gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-600">Department</label>
                    <Select value={department} onChange={(event) => setDepartment(event.target.value)}>
                      {departments.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-600">Status</label>
                    <Select value={status} onChange={(event) => setStatus(event.target.value)}>
                      {statuses.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </Select>
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <label className="text-sm font-medium text-slate-600">Search employee</label>
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name or employee ID" />
                      <Button className="shrink-0" type="button" variant="outline">
                        <Download className="h-4 w-4" />
                        Export
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-100 pb-4">
                <div>
                  <CardTitle className="text-xl text-slate-950">Daily attendance log</CardTitle>
                  <CardDescription>Showing workforce activity for {formatFullDate(selectedDate)}.</CardDescription>
                </div>
                <Badge className="border-slate-200 bg-slate-50 text-slate-600" variant="outline">
                  {filteredRows.length} employees
                </Badge>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-100">
                      <TableHead>Name</TableHead>
                      <TableHead>Employee ID</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Check-in time</TableHead>
                      <TableHead>Check-out time</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Work hours</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRows.map((row) => (
                      <TableRow key={row.id} className="border-slate-100 hover:bg-slate-50/80">
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar className="h-10 w-10 border border-slate-200 bg-slate-50">
                              <AvatarFallback>{getInitials(row.name)}</AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-medium text-slate-900">{row.name}</p>
                              <p className="text-xs text-slate-500">Active employee</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="font-medium text-slate-600">{row.employeeId}</TableCell>
                        <TableCell className="text-slate-600">{row.department}</TableCell>
                        <TableCell className="text-slate-600">{row.checkIn}</TableCell>
                        <TableCell className="text-slate-600">{row.checkOut}</TableCell>
                        <TableCell>
                          <Badge className={getStatusBadgeClassName(row.status)} variant={getStatusBadgeVariant(row.status)}>
                            {row.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-600">{row.workHours}</TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button size="icon" variant="ghost">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="border-slate-200 bg-white">
                              <DropdownMenuItem>
                                <Eye className="h-4 w-4 text-slate-500" />
                                View details
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Clock3 className="h-4 w-4 text-slate-500" />
                                Adjust time log
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <ChevronsUpDown className="h-4 w-4 text-slate-500" />
                                Change status
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-6">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg text-slate-950">Late arrivals</CardTitle>
                <CardDescription>Employees who clocked in after scheduled start time.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {lateArrivals.map((entry) => (
                  <div key={`${entry.name}-${entry.time}`} className="flex items-start justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div>
                      <p className="font-medium text-slate-900">{entry.name}</p>
                      <p className="text-sm text-slate-500">{entry.department}</p>
                    </div>
                    <Badge className="border-amber-200 bg-amber-50 text-amber-700" variant="outline">
                      {entry.time}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg text-slate-950">Missing check-outs</CardTitle>
                <CardDescription>Employees still missing an end-of-day attendance record.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {missingCheckouts.map((entry) => (
                  <div key={entry.name} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-medium text-slate-900">{entry.name}</p>
                        <p className="text-sm text-slate-500">{entry.since}</p>
                      </div>
                      <Button type="button" variant="outline" size="sm">
                        Follow up
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </aside>
        </section>
      </div>
    </div>
  )
}
