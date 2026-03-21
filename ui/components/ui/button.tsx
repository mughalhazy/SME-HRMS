import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-control)] text-sm font-semibold select-none transition-[background-color,border-color,color,box-shadow,opacity] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)] disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'border border-transparent bg-[var(--primary)] text-[var(--primary-foreground)] shadow-[var(--shadow-control)] hover:bg-[var(--primary-strong)]',
        outline:
          'border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] shadow-[var(--shadow-control)] hover:bg-[var(--surface-subtle)] hover:text-[var(--foreground)]',
        secondary:
          'border border-transparent bg-[var(--accent)] text-[var(--foreground)] shadow-[var(--shadow-control)] hover:bg-[var(--accent-strong)]',
        ghost: 'border border-transparent bg-transparent text-[var(--muted-foreground)] hover:bg-[var(--accent)] hover:text-[var(--foreground)]',
      },
      size: {
        default: 'h-10 px-4',
        sm: 'h-9 px-3.5',
        lg: 'h-11 px-5',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'

    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }
