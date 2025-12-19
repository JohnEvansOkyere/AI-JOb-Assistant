import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { ErrorBoundaryWrapper } from '@/components/ErrorBoundaryWrapper'

export const metadata: Metadata = {
  title: 'AI Voice Interview Platform',
  description: 'Conduct AI-powered voice interviews based on job descriptions and CVs',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundaryWrapper>
          <Providers>
            {children}
          </Providers>
        </ErrorBoundaryWrapper>
      </body>
    </html>
  )
}

