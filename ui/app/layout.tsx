import type { Metadata } from 'next'
import './globals.css'

import { QueryProvider } from '@/components/shared/query-provider'

export const metadata: Metadata = {
  title: 'SME HRMS',
  description: 'Frontend workspace for the SME HRMS platform.',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
