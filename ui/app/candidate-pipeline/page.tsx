import { HiringPipelineBoard } from '@/components/hiring/hiring-pipeline-board'
import AppShell from '@/components/hrms/shell/app-shell'

export default function CandidatePipelinePage() {
  return (
    <AppShell pageTitle="Candidates" pageDescription="Track active candidates, interview flow, and hiring progress in a structured talent workspace.">
      <HiringPipelineBoard />
    </AppShell>
  )
}
