/**
 * Error Boundary Wrapper
 * Client component wrapper for ErrorBoundary to use in server components
 */

'use client'

import { ErrorBoundary } from './ErrorBoundary'

export function ErrorBoundaryWrapper({ children }: { children: React.ReactNode }) {
  return <ErrorBoundary>{children}</ErrorBoundary>
}

