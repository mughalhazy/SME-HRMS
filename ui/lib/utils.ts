export type ClassValue = string | number | boolean | null | undefined | ClassDictionary | ClassArray

type ClassDictionary = Record<string, boolean | null | undefined>
type ClassArray = ClassValue[]

function toClassName(value: ClassValue): string {
  if (!value) {
    return ''
  }

  if (typeof value === 'string' || typeof value === 'number') {
    return String(value)
  }

  if (Array.isArray(value)) {
    return value.map(toClassName).filter(Boolean).join(' ')
  }

  return Object.entries(value)
    .filter(([, included]) => Boolean(included))
    .map(([className]) => className)
    .join(' ')
}

export function cn(...inputs: ClassValue[]) {
  return inputs.map(toClassName).filter(Boolean).join(' ')
}
