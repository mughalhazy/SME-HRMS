import * as React from 'react'

import { cn } from '@/lib/utils'

function Form({ className, ...props }: React.ComponentProps<'form'>) {
  return <form className={cn('space-y-6', className)} {...props} />
}

function FormField({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('space-y-2', className)} {...props} />
}

function FormLabel({ className, ...props }: React.ComponentProps<'label'>) {
  return <label className={cn('text-sm font-medium text-[var(--foreground)]', className)} {...props} />
}

function FormControl({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('space-y-2', className)} {...props} />
}

function FormDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm leading-6 text-[var(--muted-foreground)]', className)} {...props} />
}

function FormMessage({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm font-medium text-[var(--danger)]', className)} {...props} />
}

export { Form, FormControl, FormDescription, FormField, FormLabel, FormMessage }
