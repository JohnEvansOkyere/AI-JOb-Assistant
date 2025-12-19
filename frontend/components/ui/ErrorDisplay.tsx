/**
 * Error Display Component
 * User-friendly error message display with retry option
 */

'use client'

import { AlertCircle, RefreshCw, X } from 'lucide-react'
import { Button } from './Button'
import { ApiErrorHandler } from '@/lib/api/error-handler'

interface ErrorDisplayProps {
  error: any
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
  showRetry?: boolean
  title?: string
}

export function ErrorDisplay({
  error,
  onRetry,
  onDismiss,
  className = '',
  showRetry = true,
  title,
}: ErrorDisplayProps) {
  const errorMessage = ApiErrorHandler.getErrorMessage(error)
  const errorInfo = ApiErrorHandler.classifyError(error)

  // Don't show retry for client errors (4xx except 429, 408)
  const canRetry = showRetry && errorInfo.retryable && onRetry

  return (
    <div
      className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className="text-sm font-semibold text-red-800 mb-1">{title}</h3>
          )}
          <p className="text-sm text-red-700">{errorMessage}</p>
          
          {errorInfo.type === 'network' && (
            <p className="text-xs text-red-600 mt-2">
              Please check your internet connection and try again.
            </p>
          )}
          
          {errorInfo.status === 401 && (
            <p className="text-xs text-red-600 mt-2">
              You may need to log in again.
            </p>
          )}

          {canRetry && (
            <div className="mt-3">
              <Button
                size="sm"
                variant="outline"
                onClick={onRetry}
                className="border-red-300 text-red-700 hover:bg-red-100"
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Try Again
              </Button>
            </div>
          )}
        </div>
        
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 text-red-400 hover:text-red-600 transition-colors"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

interface ErrorInlineProps {
  error: any
  className?: string
}

export function ErrorInline({ error, className = '' }: ErrorInlineProps) {
  const errorMessage = ApiErrorHandler.getErrorMessage(error)
  
  return (
    <p className={`text-sm text-red-600 ${className}`} role="alert">
      {errorMessage}
    </p>
  )
}

