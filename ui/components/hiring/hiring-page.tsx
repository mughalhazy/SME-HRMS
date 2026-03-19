'use client'

import { BriefcaseBusiness, Users } from 'lucide-react'

import { HiringPipelineBoard } from '@/components/hiring/hiring-pipeline-board'
import { JobPostingsPage } from '@/components/surfaces/job-postings-page'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function HiringPage() {
  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-slate-200 bg-gradient-to-br from-white via-white to-blue-50 shadow-sm">
        <CardContent className="flex flex-col gap-5 p-6 lg:flex-row lg:items-center lg:justify-between lg:p-8">
          <div className="space-y-3">
            <Badge variant="outline" className="w-fit border-slate-200 bg-white text-slate-600">
              Hiring workspace
            </Badge>
            <div className="space-y-2">
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Requisitions and pipeline flow in one hiring route</h2>
              <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                Review open roles, move candidates through the pipeline, and keep recruiting operations aligned without bouncing between disconnected pages.
              </p>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Core views</p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">2</p>
              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">Postings + pipeline</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Primary route</p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">/hiring</p>
              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">Talent operations</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="pipeline" className="space-y-6">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="p-4">
            <TabsList className="grid h-auto w-full grid-cols-1 gap-2 bg-slate-50 p-1 md:grid-cols-2">
              <TabsTrigger value="pipeline" className="gap-2">
                <Users className="h-4 w-4" />
                Candidate pipeline
              </TabsTrigger>
              <TabsTrigger value="postings" className="gap-2">
                <BriefcaseBusiness className="h-4 w-4" />
                Job postings
              </TabsTrigger>
            </TabsList>
          </CardContent>
        </Card>

        <TabsContent value="pipeline" className="space-y-6">
          <HiringPipelineBoard />
        </TabsContent>

        <TabsContent value="postings" className="space-y-6">
          <JobPostingsPage />
        </TabsContent>
      </Tabs>
    </div>
  )
}
