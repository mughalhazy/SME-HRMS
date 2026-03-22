import * as React from 'react'

function mergeHandlers<E>(
  original?: (event: E) => void,
  incoming?: (event: E) => void,
) {
  return (event: E) => {
    original?.(event)
    incoming?.(event)
  }
}

type SlotProps = React.HTMLAttributes<HTMLElement> & {
  children: React.ReactElement
}

const Slot = React.forwardRef<HTMLElement, SlotProps>(({ children, ...props }, ref) => {
  if (!React.isValidElement(children)) {
    return null
  }

  const childProps = children.props as Record<string, unknown>
  const mergedProps: Record<string, unknown> = {
    ...props,
    ...childProps,
    className: [props.className, childProps.className].filter(Boolean).join(' '),
  }

  for (const key of Object.keys(props)) {
    if (key.startsWith('on') && typeof props[key as keyof typeof props] === 'function' && typeof childProps[key] === 'function') {
      mergedProps[key] = mergeHandlers(childProps[key] as (event: unknown) => void, props[key as keyof typeof props] as (event: unknown) => void)
    }
  }

  mergedProps.ref = ref

  return React.cloneElement(children, mergedProps)
})
Slot.displayName = 'Slot'

export { Slot }
