'use client'

import { Building2, ChevronRight, GitBranch, Plus, Users2 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type OrganizationMember = {
  name: string
  title: string
  reportsTo?: string
}

type OrganizationTeam = {
  name: string
  lead: string
  roles: number
  members: number
  membersList: OrganizationMember[]
}

type OrganizationDepartment = {
  name: string
  head: string
  roles: number
  members: number
  teams: OrganizationTeam[]
}

const departments: OrganizationDepartment[] = [
  {
    name: 'Engineering',
    head: 'Maya Chen',
    roles: 18,
    members: 286,
    teams: [
      {
        name: 'Platform',
        lead: 'Andre Silva',
        roles: 7,
        members: 92,
        membersList: [
          { name: 'Andre Silva', title: 'Engineering Manager', reportsTo: 'Maya Chen' },
          { name: 'Nina Patel', title: 'Senior Backend Engineer', reportsTo: 'Andre Silva' },
          { name: 'Leo Grant', title: 'Site Reliability Engineer', reportsTo: 'Andre Silva' },
        ],
      },
      {
        name: 'Product Engineering',
        lead: 'Hana Kim',
        roles: 6,
        members: 118,
        membersList: [
          { name: 'Hana Kim', title: 'Engineering Manager', reportsTo: 'Maya Chen' },
          { name: 'Samir Reed', title: 'Staff Frontend Engineer', reportsTo: 'Hana Kim' },
          { name: 'Ava Turner', title: 'Product Designer', reportsTo: 'Hana Kim' },
        ],
      },
      {
        name: 'Quality & Release',
        lead: 'Carla Gomez',
        roles: 5,
        members: 76,
        membersList: [
          { name: 'Carla Gomez', title: 'QA Lead', reportsTo: 'Maya Chen' },
          { name: 'Miles Brooks', title: 'Automation Engineer', reportsTo: 'Carla Gomez' },
        ],
      },
    ],
  },
  {
    name: 'People Operations',
    head: 'Jordan Ellis',
    roles: 8,
    members: 64,
    teams: [
      {
        name: 'Talent Acquisition',
        lead: 'Keira Miles',
        roles: 3,
        members: 18,
        membersList: [
          { name: 'Keira Miles', title: 'Talent Lead', reportsTo: 'Jordan Ellis' },
          { name: 'Noah Bennett', title: 'Senior Recruiter', reportsTo: 'Keira Miles' },
        ],
      },
      {
        name: 'Employee Experience',
        lead: 'Alicia Ward',
        roles: 3,
        members: 27,
        membersList: [
          { name: 'Alicia Ward', title: 'Employee Experience Manager', reportsTo: 'Jordan Ellis' },
          { name: 'Ethan Cole', title: 'HR Business Partner', reportsTo: 'Alicia Ward' },
          { name: 'Rina Das', title: 'Learning Specialist', reportsTo: 'Alicia Ward' },
        ],
      },
      {
        name: 'People Systems',
        lead: 'Marcus Hall',
        roles: 2,
        members: 19,
        membersList: [
          { name: 'Marcus Hall', title: 'HR Systems Manager', reportsTo: 'Jordan Ellis' },
          { name: 'Tessa Young', title: 'People Analytics Specialist', reportsTo: 'Marcus Hall' },
        ],
      },
    ],
  },
  {
    name: 'Revenue',
    head: 'Priya Nair',
    roles: 14,
    members: 198,
    teams: [
      {
        name: 'Enterprise Sales',
        lead: 'Daniel Ortiz',
        roles: 5,
        members: 74,
        membersList: [
          { name: 'Daniel Ortiz', title: 'Sales Director', reportsTo: 'Priya Nair' },
          { name: 'Mina Ross', title: 'Account Executive', reportsTo: 'Daniel Ortiz' },
        ],
      },
      {
        name: 'Customer Success',
        lead: 'Sofia Bennett',
        roles: 5,
        members: 83,
        membersList: [
          { name: 'Sofia Bennett', title: 'Customer Success Director', reportsTo: 'Priya Nair' },
          { name: 'Julian Cross', title: 'Senior CSM', reportsTo: 'Sofia Bennett' },
          { name: 'Elena Price', title: 'Implementation Manager', reportsTo: 'Sofia Bennett' },
        ],
      },
      {
        name: 'Revenue Operations',
        lead: 'Theo Martin',
        roles: 4,
        members: 41,
        membersList: [
          { name: 'Theo Martin', title: 'Revenue Operations Lead', reportsTo: 'Priya Nair' },
          { name: 'Ivy Chen', title: 'Sales Operations Analyst', reportsTo: 'Theo Martin' },
        ],
      },
    ],
  },
]

const executiveLeads = [
  { label: 'Chief Executive Officer', name: 'Olivia Parker' },
  { label: 'Chief Technology Officer', name: 'Maya Chen' },
  { label: 'VP People', name: 'Jordan Ellis' },
  { label: 'Chief Revenue Officer', name: 'Priya Nair' },
]

const surfaceClassName = 'border-slate-200 bg-white shadow-sm'
const badgeClassName = 'border-slate-200 bg-slate-50 text-slate-600'
const summaryItemClassName = 'space-y-1 rounded-xl border border-slate-200 bg-slate-50 p-4'
const statsClassName = 'grid gap-4 sm:grid-cols-3'

export function OrganizationPage() {
  const departmentCount = departments.length
  const teamCount = departments.reduce((total, department) => total + department.teams.length, 0)
  const roleCount = departments.reduce((total, department) => total + department.roles, 0)
  const memberCount = departments.reduce((total, department) => total + department.members, 0)

  if (departments.length === 0) {
    return (
      <div className="space-y-6">
        <Card className={surfaceClassName}>
          <CardContent className="flex flex-col gap-6 p-6">
            <div className="space-y-3">
              <Badge variant="outline" className={`w-fit ${badgeClassName}`}>
                Organization
              </Badge>
              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Organization</h1>
                <p className="max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                  Build your organization structure with departments, teams, and reporting relationships in one place.
                </p>
              </div>
            </div>
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6">
              <div className="space-y-3">
                <p className="text-base font-semibold text-slate-950">No organization structure yet</p>
                <p className="max-w-xl text-sm leading-6 text-slate-600">
                  Create your first department to start defining teams, roles, and reporting lines.
                </p>
                <Button className="w-full sm:w-auto">
                  <Plus className="h-4 w-4" />
                  Create first department
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 text-slate-950">
      <Card className={surfaceClassName}>
        <CardContent className="flex flex-col gap-6 p-6 xl:grid xl:grid-cols-12 xl:items-end">
          <div className="space-y-4 xl:col-span-9">
            <Badge variant="outline" className={`w-fit ${badgeClassName}`}>
              Organization
            </Badge>
            <p className="max-w-3xl text-sm leading-6 text-slate-600">
              View company structure by department, team, role, and reporting line with a single organized hierarchy.
            </p>
            <div className={statsClassName}>
              <div className={summaryItemClassName}>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Departments</p>
                <p className="text-2xl font-semibold tracking-tight text-slate-950">{departmentCount}</p>
              </div>
              <div className={summaryItemClassName}>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Teams</p>
                <p className="text-2xl font-semibold tracking-tight text-slate-950">{teamCount}</p>
              </div>
              <div className={summaryItemClassName}>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Members</p>
                <p className="text-2xl font-semibold tracking-tight text-slate-950">{memberCount}</p>
              </div>
            </div>
          </div>
          <div className="xl:col-span-3 xl:flex xl:justify-end">
            <Button className="w-full sm:w-auto">
              <Plus className="h-4 w-4" />
              Add department
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-12">
        <Card className={`${surfaceClassName} xl:col-span-8`}>
          <CardHeader className="space-y-3 p-6">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
              <Building2 className="h-4 w-4" />
              Organization structure
            </div>
            <div className="space-y-2">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-2xl text-slate-950">Departments, teams, and role coverage</CardTitle>
                  <p className="text-sm leading-6 text-slate-600">
                    Follow the structure from department ownership into team-level roles and individual reporting lines.
                  </p>
                </div>
                <Badge variant="outline" className={`w-fit ${badgeClassName}`}>
                  {roleCount} active roles
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            <div className="space-y-6">
              {departments.map((department, departmentIndex) => (
                <section
                  key={department.name}
                  className={departmentIndex === departments.length - 1 ? 'space-y-4' : 'space-y-4 border-b border-slate-200 pb-6'}
                >
                  <div className="grid gap-4 lg:grid-cols-12 lg:items-start">
                    <div className="space-y-2 lg:col-span-9">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-lg font-semibold text-slate-950">{department.name}</h2>
                        <Badge variant="outline" className={badgeClassName}>
                          {department.members} members
                        </Badge>
                        <Badge variant="outline" className={badgeClassName}>
                          {department.roles} roles
                        </Badge>
                      </div>
                      <p className="text-sm leading-6 text-slate-600">
                        Department head <span className="font-medium text-slate-950">{department.head}</span>
                      </p>
                    </div>
                    <div className="lg:col-span-3 lg:flex lg:justify-end">
                      <Button variant="outline" size="sm" className="w-full sm:w-auto">
                        Add role
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-4 border-l border-slate-200 pl-4 sm:pl-6">
                    {department.teams.map((team, teamIndex) => (
                      <div
                        key={team.name}
                        className={teamIndex === department.teams.length - 1 ? 'space-y-3' : 'space-y-3 border-b border-slate-200 pb-4'}
                      >
                        <div className="grid gap-3 lg:grid-cols-12 lg:items-start">
                          <div className="space-y-2 lg:col-span-8">
                            <div className="flex flex-wrap items-center gap-2">
                              <h3 className="text-base font-semibold text-slate-950">{team.name}</h3>
                              <p className="text-sm text-slate-500">Lead {team.lead}</p>
                            </div>
                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500">
                              <span>{team.members} members</span>
                              <span>{team.roles} roles</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-slate-500 lg:col-span-4 lg:justify-end">
                            <GitBranch className="h-4 w-4" />
                            <span>Team reporting</span>
                          </div>
                        </div>

                        <div className="space-y-3 pl-4">
                          {team.membersList.map((member) => (
                            <div
                              key={`${team.name}-${member.name}`}
                              className="grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-12 md:items-center"
                            >
                              <div className="space-y-1 md:col-span-7">
                                <p className="text-sm font-semibold text-slate-950">{member.name}</p>
                                <p className="text-sm text-slate-600">{member.title}</p>
                              </div>
                              <div className="flex items-center gap-2 text-sm text-slate-500 md:col-span-5 md:justify-end">
                                <ChevronRight className="h-4 w-4" />
                                <span>Reports to {member.reportsTo ?? team.lead}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6 xl:col-span-4">
          <Card className={surfaceClassName}>
            <CardHeader className="space-y-3 p-6">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
                <GitBranch className="h-4 w-4" />
                Reporting lines
              </div>
              <CardTitle className="text-xl text-slate-950">Leadership chain</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 p-6 pt-0">
              {executiveLeads.map((leader, index) => (
                <div
                  key={leader.label}
                  className={index === executiveLeads.length - 1 ? 'space-y-1' : 'space-y-1 border-b border-slate-200 pb-4'}
                >
                  <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{leader.label}</p>
                  <p className="text-sm font-semibold text-slate-950">{leader.name}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className={surfaceClassName}>
            <CardHeader className="space-y-3 p-6">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
                <Users2 className="h-4 w-4" />
                Structure details
              </div>
              <CardTitle className="text-xl text-slate-950">Coverage summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 p-6 pt-0">
              <div className={summaryItemClassName}>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Departments</p>
                <p className="text-2xl font-semibold tracking-tight text-slate-950">{departmentCount}</p>
              </div>
              <div className={summaryItemClassName}>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Teams</p>
                <p className="text-2xl font-semibold tracking-tight text-slate-950">{teamCount}</p>
              </div>
              <div className={summaryItemClassName}>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Roles</p>
                <p className="text-2xl font-semibold tracking-tight text-slate-950">{roleCount}</p>
              </div>
              <div className={summaryItemClassName}>
                <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Members</p>
                <p className="text-2xl font-semibold tracking-tight text-slate-950">{memberCount}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
