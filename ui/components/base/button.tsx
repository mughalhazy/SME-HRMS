import * as React from 'react'

import { Slot } from '@/components/base/slot'
import { cn } from '@/lib/utils'

const buttonVariantClassNames = {
  default:
    'border border-transparent bg-[var(--primary)] text-[var(--primary-foreground)] shadow-[var(--shadow-control)] hover:bg-[var(--primary-strong)]',
  outline:
    'border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] shadow-[var(--shadow-control)] hover:bg-[var(--surface-subtle)] hover:text-[var(--foreground)]',
  secondary:
    'border border-transparent bg-[var(--accent)] text-[var(--foreground)] shadow-[var(--shadow-control)] hover:bg-[var(--accent-strong)]',
  ghost: 'border border-transparent bg-transparent text-[var(--muted-foreground)] hover:bg-[var(--accent)] hover:text-[var(--foreground)]',
} as const

const buttonSizeClassNames = {
  default: 'h-10 px-4',
  sm: 'h-9 px-3.5',
  lg: 'h-11 px-5',
  icon: 'h-10 w-10',
} as const

type ButtonVariant = keyof typeof buttonVariantClassNames
type ButtonSize = keyof typeof buttonSizeClassNames

function buttonVariants({
  className,
  variant = 'default',
  size = 'default',
}: {
  className?: string
  variant?: ButtonVariant
  size?: ButtonSize
}) {
  return cn(
    'inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-control)] text-sm font-semibold select-none transition-[background-color,border-color,color,box-shadow,opacity] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)] disabled:pointer-events-none disabled:opacity-50',
    buttonVariantClassNames[variant],
    buttonSizeClassNames[size],
    className,
  )
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  variant?: ButtonVariant
  size?: ButtonSize
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, className, variant = 'default', size = 'default', asChild = false, ...props }, ref) => {
    const buttonClassName = buttonVariants({ variant, size, className })

    if (asChild) {
      if (!React.isValidElement(children)) {
        return null
      }

      return (
        <Slot className={buttonClassName} ref={ref as React.ForwardedRef<HTMLElement>} {...props}>
          {children}
        </Slot>
      )
    }

    return (
      <button className={buttonClassName} ref={ref} {...props}>
        {children}
      </button>
    )
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }
