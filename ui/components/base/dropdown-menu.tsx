'use client'

import * as React from 'react'

import { Slot } from '@/components/base/slot'
import { cn } from '@/lib/utils'

type DropdownMenuContextValue = {
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
  contentId: string
  triggerRef: React.RefObject<HTMLElement | null>
  contentRef: React.RefObject<HTMLDivElement | null>
}

const DropdownMenuContext = React.createContext<DropdownMenuContextValue | null>(null)

function useDropdownMenuContext() {
  const context = React.useContext(DropdownMenuContext)

  if (!context) {
    throw new Error('DropdownMenu components must be used within DropdownMenu')
  }

  return context
}

function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  const contentId = React.useId()
  const triggerRef = React.useRef<HTMLElement | null>(null)
  const contentRef = React.useRef<HTMLDivElement | null>(null)

  React.useEffect(() => {
    if (!open) {
      return
    }

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target as Node

      if (triggerRef.current?.contains(target) || contentRef.current?.contains(target)) {
        return
      }

      setOpen(false)
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [open])

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen, contentId, triggerRef, contentRef }}>
      <div className="relative inline-flex">{children}</div>
    </DropdownMenuContext.Provider>
  )
}

function DropdownMenuTrigger({
  children,
  className,
  asChild = false,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean }) {
  const { open, setOpen, contentId, triggerRef } = useDropdownMenuContext()

  const triggerProps = {
    'aria-controls': contentId,
    'aria-expanded': open,
    'aria-haspopup': 'menu' as const,
    className,
    onClick: (event: React.MouseEvent<HTMLButtonElement>) => {
      props.onClick?.(event)
      if (!event.defaultPrevented) {
        setOpen((current) => !current)
      }
    },
    onKeyDown: (event: React.KeyboardEvent<HTMLButtonElement>) => {
      props.onKeyDown?.(event)
      if (!event.defaultPrevented && (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault()
        setOpen(true)
      }
    },
    ref: triggerRef as React.Ref<HTMLButtonElement>,
    type: 'button' as const,
    ...props,
  }

  if (asChild) {
    if (!React.isValidElement(children)) {
      return null
    }

    return <Slot {...triggerProps}>{children}</Slot>
  }

  return <button {...triggerProps}>{children}</button>
}

function DropdownMenuContent({
  children,
  className,
  align = 'start',
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { align?: 'start' | 'end' }) {
  const { open, contentId, contentRef } = useDropdownMenuContext()

  if (!open) {
    return null
  }

  return (
    <div
      className={cn(
        'absolute top-full z-50 mt-2 min-w-44 overflow-hidden rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface)] p-1 shadow-[var(--shadow-surface)]',
        align === 'end' ? 'right-0' : 'left-0',
        className,
      )}
      id={contentId}
      ref={contentRef}
      role="menu"
      {...props}
    >
      {children}
    </div>
  )
}

function DropdownMenuItem({
  children,
  className,
  inset,
  onClick,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { inset?: boolean }) {
  const { setOpen } = useDropdownMenuContext()

  return (
    <button
      className={cn(
        'flex w-full items-center gap-2 rounded-[calc(var(--radius-control)-4px)] px-3 py-2 text-sm text-[var(--foreground)] transition-colors hover:bg-[var(--accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]',
        inset && 'pl-8',
        className,
      )}
      onClick={(event) => {
        onClick?.(event)
        if (!event.defaultPrevented) {
          setOpen(false)
        }
      }}
      role="menuitem"
      type="button"
      {...props}
    >
      {children}
    </button>
  )
}

export { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger }
