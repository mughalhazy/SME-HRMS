import { Button } from '@/components/ui/button'

export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-16 text-slate-950">
      <section className="w-full max-w-4xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">SME HRMS</p>
            <h1 className="text-4xl font-semibold tracking-tight">Next.js frontend bootstrap complete.</h1>
            <p className="max-w-2xl text-base leading-7 text-slate-600">
              App Router, Tailwind CSS, shadcn/ui primitives, and TanStack Query are wired into the
              new <code className="rounded bg-slate-100 px-1 py-0.5 text-sm">ui/</code> workspace.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button>Open dashboard</Button>
            <Button variant="outline">View API docs</Button>
          </div>
        </div>
      </section>
    </main>
  )
}
