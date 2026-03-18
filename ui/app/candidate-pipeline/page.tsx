import { HiringPipelineBoard } from '@/components/hiring/hiring-pipeline-board'
import { AppShell } from '@/components/shared/app-shell'

export default function CandidatePipelinePage() {
  return (
    <AppShell currentPath="/candidate-pipeline">
      <HiringPipelineBoard />
    </AppShell>
  )
}
