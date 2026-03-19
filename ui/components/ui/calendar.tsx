import * as React from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type CalendarEvent = {
  date: string
  label: string
}

type CalendarProps = {
  month?: Date
  selected?: Date
  onSelect?: (date: Date) => void
  className?: string
  events?: CalendarEvent[]
}

function startOfMonth(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

function addMonths(date: Date, amount: number) {
  return new Date(date.getFullYear(), date.getMonth() + amount, 1)
}

function isSameDay(left: Date, right: Date) {
  return (
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate()
  )
}

function toDateKey(date: Date) {
  return date.toISOString().slice(0, 10)
}

const weekdayLabels = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

export function Calendar({ month = new Date(), selected, onSelect, className, events = [] }: CalendarProps) {
  const [visibleMonth, setVisibleMonth] = React.useState(() => startOfMonth(month))

  React.useEffect(() => {
    setVisibleMonth(startOfMonth(month))
  }, [month])

  const eventDates = React.useMemo(() => new Set(events.map((event) => event.date)), [events])

  const days = React.useMemo(() => {
    const monthStart = startOfMonth(visibleMonth)
    const calendarStart = new Date(monthStart)
    calendarStart.setDate(monthStart.getDate() - monthStart.getDay())

    return Array.from({ length: 42 }, (_, index) => {
      const date = new Date(calendarStart)
      date.setDate(calendarStart.getDate() + index)
      return date
    })
  }, [visibleMonth])

  return (
    <div className={cn('rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] p-3 shadow-[var(--shadow-control)]', className)}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <Button type="button" variant="ghost" size="icon" className="h-8 w-8" onClick={() => setVisibleMonth((current) => addMonths(current, -1))}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div className="text-sm font-semibold text-[var(--foreground)]">
          {visibleMonth.toLocaleString('en-US', { month: 'long', year: 'numeric' })}
        </div>
        <Button type="button" variant="ghost" size="icon" className="h-8 w-8" onClick={() => setVisibleMonth((current) => addMonths(current, 1))}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
        {weekdayLabels.map((label) => (
          <div key={label} className="py-1">
            {label}
          </div>
        ))}
      </div>

      <div className="mt-1 grid grid-cols-7 gap-1">
        {days.map((date) => {
          const inMonth = date.getMonth() === visibleMonth.getMonth()
          const selectedDay = selected ? isSameDay(date, selected) : false
          const hasEvent = eventDates.has(toDateKey(date))

          return (
            <button
              key={date.toISOString()}
              type="button"
              onClick={() => onSelect?.(date)}
              className={cn(
                'relative flex h-10 items-center justify-center rounded-[calc(var(--radius-control)-2px)] text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]',
                inMonth ? 'text-[var(--foreground)] hover:bg-[var(--accent)]' : 'text-slate-300',
                selectedDay && 'bg-[var(--primary)] font-semibold text-[var(--primary-foreground)] hover:bg-[var(--primary-strong)]',
              )}
            >
              <span>{date.getDate()}</span>
              {hasEvent ? (
                <span
                  className={cn(
                    'absolute bottom-1 h-1.5 w-1.5 rounded-full',
                    selectedDay ? 'bg-[var(--primary-foreground)]' : 'bg-amber-500',
                  )}
                />
              ) : null}
            </button>
          )
        })}
      </div>
    </div>
  )
}
