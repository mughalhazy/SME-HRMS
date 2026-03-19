'use client'

import * as React from 'react'

import { cn } from '@/lib/utils'

type SwitchProps = Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> & {
  checked?: boolean
  defaultChecked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ className, checked, defaultChecked = false, onCheckedChange, disabled, type = 'button', ...props }, ref) => {
    const [internalChecked, setInternalChecked] = React.useState(defaultChecked)
    const isControlled = checked !== undefined
    const isChecked = isControlled ? checked : internalChecked

    const toggle = () => {
      if (disabled) {
        return
      }

      const nextChecked = !isChecked

      if (!isControlled) {
        setInternalChecked(nextChecked)
      }

      onCheckedChange?.(nextChecked)
    }

    return (
      <button
        aria-checked={isChecked}
        className={cn(
          'inline-flex h-6 w-11 shrink-0 items-center rounded-full border border-transparent p-0.5 shadow-[var(--shadow-control)] transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)] disabled:cursor-not-allowed disabled:opacity-50',
          isChecked ? 'bg-[var(--primary)]' : 'bg-slate-200',
          className,
        )}
        disabled={disabled}
        onClick={toggle}
        ref={ref}
        role="switch"
        type={type}
        {...props}
      >
        <span
          className={cn(
            'block h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200',
            isChecked ? 'translate-x-5' : 'translate-x-0',
          )}
        />
      </button>
    )
  },
)
Switch.displayName = 'Switch'

export { Switch }
