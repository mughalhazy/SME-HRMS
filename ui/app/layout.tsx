import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import './globals.css'

import { QueryProvider } from '@/components/shared/query-provider'

export const metadata: Metadata = {
  title: 'SME HRMS',
  description: 'Frontend workspace for the SME HRMS platform.',
}

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
