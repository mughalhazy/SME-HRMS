import * as React from 'react'

import { cn } from '@/lib/utils'

function Avatar({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full border border-[var(--border)] bg-[var(--surface)]', className)} {...props} />
}

function AvatarImage({ className, alt = '', ...props }: React.ImgHTMLAttributes<HTMLImageElement>) {
  return <img alt={alt} className={cn('h-full w-full object-cover', className)} {...props} />
}

function AvatarFallback({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('flex h-full w-full items-center justify-center bg-slate-100 text-sm font-semibold text-slate-700', className)} {...props} />
}

export { Avatar, AvatarFallback, AvatarImage }
