'use client'

import { useMemo, useState } from 'react'
import { Building2, ChevronDown, ChevronsLeft, ChevronsRight, MapPin, MoreHorizontal, Plus, Search, UserCircle2 } from 'lucide-react'

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
    case 'Remote':
      return 'default'
    default:
      return 'outline'
  }
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

  return (
    <section className="space-y-6 rounded-[var(--radius-surface)] border border-slate-200 bg-white p-6 shadow-sm">
      <header className="flex flex-col gap-4 border-b border-slate-100 pb-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">Employee directory</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">Employees</h1>
        </div>
        <Button className="bg-slate-950 text-white hover:bg-slate-800">
          <Plus className="h-4 w-4" />
          Add Employee
        </Button>
      </header>

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.7fr)_repeat(3,minmax(0,0.85fr))]">
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
              className="border-slate-200 bg-white pl-9"
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
              className="border-slate-200 bg-white pl-9"
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
              className="border-slate-200 bg-white pl-9"
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

      <div className="overflow-hidden rounded-2xl border border-slate-200">
        <Table>
          <TableHeader className="bg-slate-50">
            <TableRow className="hover:bg-transparent hover:shadow-none">
              <TableHead>Name</TableHead>
              <TableHead>Employee ID</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Manager</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Join Date</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody className="[&_tr:nth-child(even)]:bg-white">
            {paginatedEmployees.length > 0 ? (
              paginatedEmployees.map((employee) => (
                <TableRow key={employee.id} className="bg-white hover:bg-slate-50">
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar className="h-10 w-10 border-slate-200 bg-slate-50">
                        <AvatarFallback className="bg-slate-100 text-slate-700">{initials(employee.name)}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-slate-950">{employee.name}</p>
                        <p className="text-xs text-slate-500">{employee.email}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="font-medium text-slate-700">{employee.id}</TableCell>
                  <TableCell className="text-slate-600">{employee.department}</TableCell>
                  <TableCell className="text-slate-600">{employee.role}</TableCell>
                  <TableCell className="text-slate-600">{employee.manager}</TableCell>
                  <TableCell>
                    <Badge
                      className={cn(
                        'border px-2.5 py-1 font-medium',
                        employee.status === 'On Leave' && 'border-amber-200 bg-amber-50 text-amber-700',
                        employee.status === 'Probation' && 'border-slate-200 bg-slate-100 text-slate-700',
                        employee.status === 'Remote' && 'border-blue-200 bg-blue-50 text-blue-700',
                      )}
                      variant={statusVariant(employee.status)}
                    >
                      {employee.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-600">{formatJoinDate(employee.joinDate)}</TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button className="border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-950" size="icon" variant="ghost">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>View Profile</DropdownMenuItem>
                        <DropdownMenuItem>Edit Employee</DropdownMenuItem>
                        <DropdownMenuItem>Send Message</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow className="bg-white hover:bg-white">
                <TableCell className="py-12 text-center text-sm text-slate-500" colSpan={8}>
                  No employees match the selected filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <footer className="flex flex-col gap-4 border-t border-slate-100 pt-5 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-slate-500">
          Showing <span className="font-medium text-slate-900">{startResult}-{endResult}</span> of{' '}
          <span className="font-medium text-slate-900">{filteredEmployees.length}</span> employees
        </p>

        <div className="flex items-center gap-2">
          <Button
            className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
            disabled={currentPage === 1}
            onClick={() => setPage((value) => Math.max(1, value - 1))}
            variant="outline"
          >
            <ChevronsLeft className="h-4 w-4" />
            Previous
          </Button>
          <div className="rounded-[var(--radius-control)] border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-600">
            Page {currentPage} of {totalPages}
          </div>
          <Button
            className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
            disabled={currentPage === totalPages}
            onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
            variant="outline"
          >
            Next
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </footer>
    </section>
  )
}
