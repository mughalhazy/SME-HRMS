'use client'

import { Building2, Layers3 } from 'lucide-react'

import { PeopleStructurePage } from '@/components/employees/people-structure-page'
import { Departments } from '@/components/surfaces/Departments'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function OrganizationPage() {
  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-slate-200 bg-gradient-to-br from-white via-white to-slate-50 shadow-sm">
        <CardContent className="flex flex-col gap-5 p-6 lg:flex-row lg:items-center lg:justify-between lg:p-8">
          <div className="space-y-3">
            <Badge variant="outline" className="w-fit border-slate-200 bg-slate-50 text-slate-600">
              Organization workspace
            </Badge>
            <div className="space-y-2">
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Organizational structure without fragmented routes</h2>
              <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                Switch between departments and role distribution from one page so navigation stays clean while workforce structure remains fully visible.
              </p>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Primary views</p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">2</p>
              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">Departments + roles</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Navigation depth</p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">1 route</p>
              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">/organization</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="departments" className="space-y-6">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="p-4">
            <TabsList className="grid h-auto w-full grid-cols-1 gap-2 bg-slate-50 p-1 md:grid-cols-2">
              <TabsTrigger value="departments" className="gap-2">
                <Building2 className="h-4 w-4" />
                Departments
              </TabsTrigger>
              <TabsTrigger value="roles" className="gap-2">
                <Layers3 className="h-4 w-4" />
                Roles
              </TabsTrigger>
            </TabsList>
          </CardContent>
        </Card>

        <TabsContent value="departments" className="space-y-6">
          <Departments />
        </TabsContent>

        <TabsContent value="roles" className="space-y-6">
          <PeopleStructurePage mode="roles" />
        </TabsContent>
      </Tabs>
    </div>
  )
}
