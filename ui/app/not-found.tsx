import Link from 'next/link'
import { Compass, Home, SearchX } from 'lucide-react'

import AppShell from '@/components/hrms/shell/app-shell'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { pageIconChipClassName } from '@/components/ui/page'

export default function NotFound() {
  return (
    <AppShell pageTitle="Page not found" pageDescription="The route you requested is not available in the HRMS workspace.">
      <div className="flex min-h-[70vh] items-center justify-center">
        <Card className="w-full max-w-2xl">
          <CardContent className="flex flex-col items-center gap-6 px-6 py-12 text-center sm:px-6">
            <div className={pageIconChipClassName}>
              <SearchX className="h-8 w-8" />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-400">404</p>
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">This workspace page could not be found</h2>
              <p className="text-sm leading-6 text-slate-600 sm:text-base">
                Use the main navigation to continue working across dashboard, employees, operations, and talent modules.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-3">
              <Button asChild>
                <Link href="/dashboard">
                  <Home className="h-4 w-4" />
                  Go to dashboard
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/employees">
                  <Compass className="h-4 w-4" />
                  Open employees
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
