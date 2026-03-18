import * as React from 'react'

import { cn } from '@/lib/utils'

function Table({ className, ...props }: React.ComponentProps<'table'>) {
  return (
    <div className="w-full overflow-x-auto rounded-2xl">
      <table className={cn('w-full caption-bottom text-sm', className)} {...props} />
    </div>
  )
}

function TableHeader({ className, ...props }: React.ComponentProps<'thead'>) {
  return <thead className={cn('sticky top-0 z-10 bg-[var(--surface)] [&_tr]:border-b [&_tr]:border-[var(--border)]', className)} {...props} />
}

function TableBody({ className, ...props }: React.ComponentProps<'tbody'>) {
  return <tbody className={cn('[&_tr:last-child]:border-0 [&_tr:nth-child(even)]:bg-slate-50/40', className)} {...props} />
}

function TableRow({ className, ...props }: React.ComponentProps<'tr'>) {
  return (
    <tr
      className={cn('border-b border-[var(--border)] transition-colors duration-150 hover:bg-[var(--accent)]/70', className)}
      {...props}
    />
  )
}

function TableHead({ className, ...props }: React.ComponentProps<'th'>) {
  return (
    <th
      className={cn('h-11 px-4 text-left align-middle text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted-foreground)]', className)}
      {...props}
    />
  )
}

function TableCell({ className, ...props }: React.ComponentProps<'td'>) {
  return <td className={cn('px-4 py-3 align-middle text-[var(--foreground)]', className)} {...props} />
}

function TableCaption({ className, ...props }: React.ComponentProps<'caption'>) {
  return <caption className={cn('mt-4 text-sm text-[var(--muted-foreground)]', className)} {...props} />
}

export { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow }
