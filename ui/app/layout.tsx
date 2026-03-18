import type { Metadata } from 'next'
import './globals.css'

import { QueryProvider } from '@/components/shared/query-provider'

export const metadata: Metadata = {
  title: 'SME HRMS UI System',
  description: 'Enterprise-grade Next.js and shadcn-style UI foundation for SME HRMS.',
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
