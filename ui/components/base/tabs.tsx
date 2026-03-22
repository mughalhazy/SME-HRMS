'use client'

import * as React from 'react'

import { cn } from '@/lib/utils'

type TabsContextValue = {
  value: string
  setValue: React.Dispatch<React.SetStateAction<string>>
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

function useTabsContext() {
  const context = React.useContext(TabsContext)

  if (!context) {
    throw new Error('Tabs components must be used within <Tabs>.')
  }

  return context
}

function Tabs({
  children,
  defaultValue,
  className,
}: {
  children: React.ReactNode
  defaultValue: string
  className?: string
}) {
  const [value, setValue] = React.useState(defaultValue)

  return (
    <TabsContext.Provider value={{ value, setValue }}>
      <div className={cn('space-y-6', className)}>{children}</div>
    </TabsContext.Provider>
  )
}

function TabsList({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('inline-flex w-full flex-wrap gap-2 rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface-subtle)] p-2', className)}
      {...props}
    />
  )
}

function TabsTrigger({ value, className, children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { value: string }) {
  const { value: selectedValue, setValue } = useTabsContext()

  return (
    <button
      className={cn(
        'inline-flex min-h-10 min-w-[9rem] items-center justify-center rounded-[calc(var(--radius-control)-2px)] px-4 py-2 text-sm font-semibold transition-[background-color,color,box-shadow,opacity] duration-150 ease-out active:opacity-90',
        selectedValue === value
          ? 'bg-[var(--surface)] text-[var(--foreground)] shadow-[var(--shadow-control)]'
          : 'text-[var(--muted-foreground)] hover:bg-[var(--accent)] hover:text-[var(--foreground)]',
        className,
      )}
      onClick={() => setValue(value)}
      type="button"
      {...props}
    >
      {children}
    </button>
  )
}

function TabsContent({ value, className, children, ...props }: React.HTMLAttributes<HTMLDivElement> & { value: string }) {
  const { value: selectedValue } = useTabsContext()

  if (selectedValue !== value) {
    return null
  }

  return (
    <div className={cn('animate-[surface-enter_180ms_ease-out] space-y-6', className)} {...props}>
      {children}
    </div>
  )
}

export { Tabs, TabsContent, TabsList, TabsTrigger }
