'use client'

import * as React from 'react'

import { cn } from '@/lib/utils'

const DialogContext = React.createContext<{
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
} | null>(null)

function useDialogContext() {
  const context = React.useContext(DialogContext)

  if (!context) {
    throw new Error('Dialog components must be used within <Dialog>.')
  }

  return context
}

function Dialog({ children, defaultOpen = false }: { children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = React.useState(defaultOpen)

  return <DialogContext.Provider value={{ open, setOpen }}>{children}</DialogContext.Provider>
}

type DialogActionChild = React.ReactElement<{ onClick?: (event: React.MouseEvent) => void }>

function DialogTrigger({ children }: { children: DialogActionChild }) {
  const { setOpen } = useDialogContext()

  return React.cloneElement(children, {
    onClick: (event: React.MouseEvent) => {
      children.props.onClick?.(event)
      setOpen(true)
    },
  })
}

function DialogClose({ children }: { children: DialogActionChild }) {
  const { setOpen } = useDialogContext()

  return React.cloneElement(children, {
    onClick: (event: React.MouseEvent) => {
      children.props.onClick?.(event)
      setOpen(false)
    },
  })
}

function DialogContent({ className, children }: { className?: string; children: React.ReactNode }) {
  const { open, setOpen } = useDialogContext()

  React.useEffect(() => {
    if (!open) {
      return undefined
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }

    window.addEventListener('keydown', handleEscape)

    return () => window.removeEventListener('keydown', handleEscape)
  }, [open, setOpen])

  if (!open) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4">
      <button aria-label="Close dialog overlay" className="absolute inset-0 cursor-default" onClick={() => setOpen(false)} />
      <div
        className={cn(
          'relative z-10 w-full max-w-lg rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-surface)]',
          className,
        )}
        role="dialog"
        aria-modal="true"
      >
        {children}
      </div>
    </div>
  )
}

function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('space-y-2', className)} {...props} />
}

function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn('text-xl font-semibold text-[var(--foreground)]', className)} {...props} />
}

function DialogDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm leading-6 text-[var(--muted-foreground)]', className)} {...props} />
}

function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mt-6 flex flex-wrap justify-end gap-3', className)} {...props} />
}

export { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger }
