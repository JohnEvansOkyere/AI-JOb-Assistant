import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { ErrorBoundaryWrapper } from '@/components/ErrorBoundaryWrapper'

export const metadata: Metadata = {
  title: 'VeloxaRecruit - AI-Powered Recruitment Platform',
  description: 'Transform hiring with AI voice interviews. Screen faster, hire smarter with VeloxaRecruit by Veloxa Technologies Ltd.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <ErrorBoundaryWrapper>
          <Providers>
            {children}
          </Providers>
        </ErrorBoundaryWrapper>
      </body>
    </html>
  )
}

