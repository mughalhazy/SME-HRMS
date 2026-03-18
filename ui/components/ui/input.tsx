import * as React from 'react'

import { cn } from '@/lib/utils'

export const controlClassName =
  'flex w-full rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface)] px-3.5 text-sm text-[var(--foreground)] shadow-[var(--shadow-control)] transition-[border-color,box-shadow,background-color,color] duration-150 placeholder:text-[var(--muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)] disabled:cursor-not-allowed disabled:opacity-50 aria-[invalid=true]:border-[color:color-mix(in_srgb,var(--danger)_55%,white)] aria-[invalid=true]:ring-[color:color-mix(in_srgb,var(--danger)_18%,transparent)]'

export const inputClassName = cn(controlClassName, 'h-10 py-2.5')
export const selectClassName = cn(inputClassName, 'appearance-none')
export const textareaClassName = cn(controlClassName, 'min-h-28 py-3')

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<'input'>>(({ className, ...props }, ref) => {
  return <input className={cn(inputClassName, className)} ref={ref} {...props} />
})
Input.displayName = 'Input'

const Select = React.forwardRef<HTMLSelectElement, React.ComponentProps<'select'>>(({ className, ...props }, ref) => {
  return <select className={cn(selectClassName, className)} ref={ref} {...props} />
})
Select.displayName = 'Select'

const Textarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<'textarea'>>(({ className, ...props }, ref) => {
  return <textarea className={cn(textareaClassName, className)} ref={ref} {...props} />
})
Textarea.displayName = 'Textarea'

export { Input, Select, Textarea }
