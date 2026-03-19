'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import {
  Building2,
  ChevronDown,
  ChevronsLeft,
  ChevronsRight,
  MapPin,
  MoreHorizontal,
  Plus,
  Search,
  UserCircle2,
  Users,
} from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Input, Select } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

type EmployeeStatus = 'Active' | 'Remote' | 'On Leave' | 'Probation'

type EmployeeRecord = {
  id: string
  name: string
  department: 'Engineering' | 'Human Resources' | 'Finance' | 'Design' | 'Operations' | 'Sales'
  role: string
  manager: string
  status: EmployeeStatus
  joinDate: string
  location: 'New York, USA' | 'Austin, USA' | 'Chicago, USA' | 'London, UK' | 'Toronto, Canada'
  email: string
}

const employees: EmployeeRecord[] = [
  {
    id: 'EMP-1048',
    name: 'Olivia Bennett',
    department: 'Engineering',
    role: 'Senior Frontend Engineer',
    manager: 'Marcus Hill',
    status: 'Active',
    joinDate: '2022-03-14',
    location: 'New York, USA',
    email: 'olivia.bennett@acmehr.com',
  },
  {
    id: 'EMP-1052',
    name: 'Daniel Kim',
    department: 'Finance',
    role: 'Financial Analyst',
    manager: 'Priya Shah',
    status: 'Remote',
    joinDate: '2021-09-06',
    location: 'Toronto, Canada',
    email: 'daniel.kim@acmehr.com',
  },
  {
    id: 'EMP-1061',
    name: 'Ava Thompson',
    department: 'Human Resources',
    role: 'HR Business Partner',
    manager: 'Leah Morgan',
    status: 'Active',
    joinDate: '2023-01-23',
    location: 'Chicago, USA',
    email: 'ava.thompson@acmehr.com',
  },
  {
    id: 'EMP-1067',
    name: 'Ethan Carter',
    department: 'Operations',
    role: 'Operations Coordinator',
    manager: 'Monica Reyes',
    status: 'Probation',
    joinDate: '2024-11-04',
    location: 'Austin, USA',
    email: 'ethan.carter@acmehr.com',
  },
  {
    id: 'EMP-1074',
    name: 'Sophia Martinez',
    department: 'Design',
    role: 'Product Designer',
    manager: 'Nina Walker',
    status: 'Remote',
    joinDate: '2022-07-18',
    location: 'London, UK',
    email: 'sophia.martinez@acmehr.com',
  },
  {
    id: 'EMP-1083',
    name: 'Noah Patel',
    department: 'Engineering',
    role: 'Backend Engineer',
    manager: 'Marcus Hill',
    status: 'Active',
    joinDate: '2020-05-11',
    location: 'Austin, USA',
    email: 'noah.patel@acmehr.com',
  },
  {
    id: 'EMP-1090',
    name: 'Grace Liu',
    department: 'Sales',
    role: 'Account Executive',
    manager: 'Trevor Miles',
    status: 'On Leave',
    joinDate: '2021-11-29',
    location: 'New York, USA',
    email: 'grace.liu@acmehr.com',
  },
  {
    id: 'EMP-1098',
    name: 'Liam Foster',
    department: 'Operations',
    role: 'Facilities Lead',
    manager: 'Monica Reyes',
    status: 'Active',
    joinDate: '2019-08-12',
    location: 'Chicago, USA',
    email: 'liam.foster@acmehr.com',
  },
  {
    id: 'EMP-1106',
    name: 'Charlotte Reed',
    department: 'Human Resources',
    role: 'Talent Acquisition Specialist',
    manager: 'Leah Morgan',
    status: 'Active',
    joinDate: '2023-04-17',
    location: 'Toronto, Canada',
    email: 'charlotte.reed@acmehr.com',
  },
  {
    id: 'EMP-1115',
    name: 'James Walker',
    department: 'Finance',
    role: 'Payroll Manager',
    manager: 'Priya Shah',
    status: 'Remote',
    joinDate: '2020-10-08',
    location: 'London, UK',
    email: 'james.walker@acmehr.com',
  },
  {
    id: 'EMP-1124',
    name: 'Mia Gonzalez',
    department: 'Sales',
    role: 'Sales Operations Analyst',
    manager: 'Trevor Miles',
    status: 'Active',
    joinDate: '2022-02-21',
    location: 'Austin, USA',
    email: 'mia.gonzalez@acmehr.com',
  },
  {
    id: 'EMP-1138',
    name: 'Benjamin Clark',
    department: 'Engineering',
    role: 'QA Automation Engineer',
    manager: 'Marcus Hill',
    status: 'Probation',
    joinDate: '2025-01-13',
    location: 'New York, USA',
    email: 'benjamin.clark@acmehr.com',
  },
]

const departments = ['All Departments', 'Engineering', 'Human Resources', 'Finance', 'Design', 'Operations', 'Sales'] as const
const statuses = ['All Statuses', 'Active', 'Remote', 'On Leave', 'Probation'] as const
const locations = ['All Locations', 'New York, USA', 'Austin, USA', 'Chicago, USA', 'London, UK', 'Toronto, Canada'] as const
const PAGE_SIZE = 6

function formatJoinDate(date: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(date))
}

function initials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function statusVariant(status: EmployeeStatus) {
  switch (status) {
    case 'Active':
      return 'success'
    case 'On Leave':
      return 'outline'
    case 'Probation':
      return 'outline'
    default:
      return 'default'
  }
}

function statusClassName(status: EmployeeStatus) {
  switch (status) {
    case 'Active':
      return 'border-transparent bg-emerald-50 text-emerald-700'
    case 'Remote':
      return 'border-transparent bg-sky-50 text-sky-700'
    case 'On Leave':
      return 'border-transparent bg-amber-50 text-amber-700'
    case 'Probation':
      return 'border-transparent bg-rose-50 text-rose-700'
  }
}

function summaryMetrics(records: EmployeeRecord[]) {
  const activeCount = records.filter((employee) => employee.status === 'Active').length
  const remoteCount = records.filter((employee) => employee.status === 'Remote').length
  const departmentsCount = new Set(records.map((employee) => employee.department)).size

  return [
    {
      label: 'Total employees',
      value: records.length,
      tone: 'text-slate-950',
    },
    {
      label: 'Active employees',
      value: activeCount,
      tone: 'text-emerald-700',
    },
    {
      label: 'Remote employees',
      value: remoteCount,
      tone: 'text-sky-700',
    },
    {
      label: 'Departments',
      value: departmentsCount,
      tone: 'text-slate-950',
    },
  ]
}

export function EmployeeList() {
  const [search, setSearch] = useState('')
  const [department, setDepartment] = useState<(typeof departments)[number]>('All Departments')
  const [status, setStatus] = useState<(typeof statuses)[number]>('All Statuses')
  const [location, setLocation] = useState<(typeof locations)[number]>('All Locations')
  const [page, setPage] = useState(1)

  const filteredEmployees = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    return employees.filter((employee) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        [employee.name, employee.id, employee.role, employee.manager, employee.department, employee.location, employee.email]
          .join(' ')
          .toLowerCase()
          .includes(normalizedSearch)

      const matchesDepartment = department === 'All Departments' || employee.department === department
      const matchesStatus = status === 'All Statuses' || employee.status === status
      const matchesLocation = location === 'All Locations' || employee.location === location

      return matchesSearch && matchesDepartment && matchesStatus && matchesLocation
    })
  }, [department, location, search, status])

  const totalPages = Math.max(1, Math.ceil(filteredEmployees.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const paginatedEmployees = filteredEmployees.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const startResult = filteredEmployees.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1
  const endResult = Math.min(currentPage * PAGE_SIZE, filteredEmployees.length)
  const metrics = useMemo(() => summaryMetrics(filteredEmployees), [filteredEmployees])

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div className="space-y-3">
            <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-600">
              Employee directory
            </Badge>
            <div className="space-y-2">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Employees</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                    Review workforce coverage, scan headcount changes quickly, and move into employee actions without losing context.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:items-center">
            <Button variant="outline" className="border-slate-200 bg-white hover:bg-slate-50">
              Export roster
            </Button>
            <Button asChild className="shadow-sm">
              <Link href="/employees/new">
                <Plus className="h-4 w-4" />
                Add Employee
              </Link>
            </Button>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-lg border border-slate-200 bg-slate-50/70 px-4 py-4">
              <p className="text-sm font-medium text-slate-500">{metric.label}</p>
              <p className={cn('mt-2 text-2xl font-semibold tracking-tight', metric.tone)}>{metric.value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-6">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-1">
              <h3 className="text-lg font-semibold text-slate-950">Filters</h3>
              <p className="text-sm text-slate-500">Refine by employee, status, department, or location.</p>
            </div>
            <div className="text-sm text-slate-500">
              Showing <span className="font-semibold text-slate-950">{startResult}-{endResult}</span> of{' '}
              <span className="font-semibold text-slate-950">{filteredEmployees.length}</span> employees
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_repeat(3,minmax(0,0.85fr))]">
            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              <span>Search</span>
              <span className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  className="border-slate-200 bg-white pl-9"
                  onChange={(event) => {
                    setSearch(event.target.value)
                    setPage(1)
                  }}
                  placeholder="Search by employee, role, ID, or manager"
                  value={search}
                />
              </span>
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              <span>Department</span>
              <div className="relative">
                <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Select
                  className="border-slate-200 bg-white pl-9 pr-10"
                  onChange={(event) => {
                    setDepartment(event.target.value as (typeof departments)[number])
                    setPage(1)
                  }}
                  value={department}
                >
                  {departments.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              </div>
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              <span>Status</span>
              <div className="relative">
                <UserCircle2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Select
                  className="border-slate-200 bg-white pl-9 pr-10"
                  onChange={(event) => {
                    setStatus(event.target.value as (typeof statuses)[number])
                    setPage(1)
                  }}
                  value={status}
                >
                  {statuses.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              </div>
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              <span>Location</span>
              <div className="relative">
                <MapPin className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Select
                  className="border-slate-200 bg-white pl-9 pr-10"
                  onChange={(event) => {
                    setLocation(event.target.value as (typeof locations)[number])
                    setPage(1)
                  }}
                  value={location}
                >
                  {locations.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              </div>
            </label>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg border border-slate-200">
          <Table>
            <TableHeader className="bg-slate-50">
              <TableRow className="hover:bg-slate-50">
                <TableHead className="w-[28%]">Employee</TableHead>
                <TableHead className="w-[16%]">Department</TableHead>
                <TableHead className="w-[20%]">Role & Manager</TableHead>
                <TableHead className="w-[14%]">Status</TableHead>
                <TableHead className="w-[14%]">Joined</TableHead>
                <TableHead className="w-[8%] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedEmployees.length > 0 ? (
                paginatedEmployees.map((employee) => (
                  <TableRow key={employee.id} className="hover:bg-gray-50">
                    <TableCell className="py-4 align-top">
                      <div className="flex items-start gap-3">
                        <Avatar className="mt-0.5 h-10 w-10 border border-slate-200 bg-slate-100">
                          <AvatarFallback className="bg-slate-100 text-xs font-semibold text-slate-700">{initials(employee.name)}</AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 space-y-1">
                          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                            <p className="font-semibold text-slate-950">{employee.name}</p>
                            <span className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">{employee.id}</span>
                          </div>
                          <p className="truncate text-sm text-slate-600">{employee.email}</p>
                          <p className="text-sm text-slate-500">{employee.location}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="py-4 align-top">
                      <div className="space-y-1">
                        <p className="font-medium text-slate-900">{employee.department}</p>
                        <p className="text-sm text-slate-500">Regional team</p>
                      </div>
                    </TableCell>
                    <TableCell className="py-4 align-top">
                      <div className="space-y-1">
                        <p className="font-medium text-slate-900">{employee.role}</p>
                        <p className="text-sm text-slate-500">Manager: {employee.manager}</p>
                      </div>
                    </TableCell>
                    <TableCell className="py-4 align-top">
                      <Badge className={cn('rounded-full px-2.5 py-1 text-xs font-semibold', statusClassName(employee.status))} variant={statusVariant(employee.status)}>
                        {employee.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="py-4 align-top text-sm text-slate-600">{formatJoinDate(employee.joinDate)}</TableCell>
                    <TableCell className="py-4 align-top">
                      <div className="flex justify-end">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="text-slate-500 hover:bg-slate-100 hover:text-slate-900" aria-label={`Open actions for ${employee.name}`}>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-44">
                            <DropdownMenuItem>View profile</DropdownMenuItem>
                            <DropdownMenuItem>Edit employee</DropdownMenuItem>
                            <DropdownMenuItem>Assign review</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow className="hover:bg-white">
                  <TableCell colSpan={6} className="py-12 text-center text-sm text-slate-500">
                    No employees match the selected filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        <div className="flex flex-col gap-4 border-t border-slate-200 pt-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
            <div className="rounded-full bg-white p-2 text-slate-500 shadow-sm">
              <Users className="h-4 w-4" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-900">Directory coverage</p>
              <p className="text-sm text-slate-500">
                Showing {startResult}-{endResult} of {filteredEmployees.length} matching employees across {totalPages} pages.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <p className="text-sm text-slate-500">
              Page <span className="font-semibold text-slate-950">{currentPage}</span> of <span className="font-semibold text-slate-950">{totalPages}</span>
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="border-slate-200 bg-white hover:bg-slate-50"
                disabled={currentPage === 1}
                onClick={() => setPage((previous) => Math.max(1, previous - 1))}
              >
                <ChevronsLeft className="h-4 w-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-slate-200 bg-white hover:bg-slate-50"
                disabled={currentPage === totalPages}
                onClick={() => setPage((previous) => Math.min(totalPages, previous + 1))}
              >
                Next
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
