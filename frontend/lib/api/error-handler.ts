/**
 * Error Handling Utilities
 * Provides user-friendly error messages and error classification
 */

export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: any
}

export class ApiErrorHandler {
  /**
   * Get user-friendly error message from API error
   */
  static getErrorMessage(error: any): string {
    // If it's already a string, return it
    if (typeof error === 'string') {
      return error
    }

    // If it's an Error object with a message
    if (error instanceof Error) {
      return this.formatErrorMessage(error.message)
    }

    // If it has a response object (from API)
    if (error?.response) {
      const response = error.response
      
      // Try different error message fields
      const message = 
        response.detail ||
        response.message ||
        response.error ||
        (typeof response.detail === 'object' ? response.detail?.message : null) ||
        'An error occurred'

      return this.formatErrorMessage(message)
    }

    // If it has a message property
    if (error?.message) {
      return this.formatErrorMessage(error.message)
    }

    // Default fallback
    return 'An unexpected error occurred. Please try again.'
  }

  /**
   * Format error message to be user-friendly
   */
  private static formatErrorMessage(message: string): string {
    if (!message) return 'An error occurred'

    // Remove technical details that users don't need
    let formatted = message

    // Replace common technical errors with user-friendly messages
    const replacements: Record<string, string> = {
      'NetworkError': 'Network connection failed. Please check your internet connection.',
      'Failed to fetch': 'Unable to connect to the server. Please check your internet connection.',
      'timeout': 'Request timed out. Please try again.',
      'ECONNREFUSED': 'Unable to connect to the server. Please ensure the server is running.',
      '401': 'Your session has expired. Please log in again.',
      '403': 'You do not have permission to perform this action.',
      '404': 'The requested resource was not found.',
      '413': 'File is too large. Please upload a smaller file.',
      '415': 'File type not supported. Please use a supported file format.',
      '422': 'Invalid input. Please check your information and try again.',
      '429': 'Too many requests. Please wait a moment and try again.',
      '500': 'Server error. Please try again later.',
      '502': 'Service temporarily unavailable. Please try again later.',
      '503': 'Service unavailable. Please try again later.',
    }

    // Check for status codes in message
    for (const [key, value] of Object.entries(replacements)) {
      if (formatted.includes(key) || formatted.toLowerCase().includes(key.toLowerCase())) {
        return value
      }
    }

    // Capitalize first letter if needed
    if (formatted.length > 0) {
      formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1)
    }

    return formatted
  }

  /**
   * Check if error is retryable
   */
  static isRetryable(error: any): boolean {
    // Network errors are retryable
    if (error?.message?.includes('NetworkError') || 
        error?.message?.includes('Failed to fetch') ||
        error?.message?.includes('timeout')) {
      return true
    }

    // 5xx errors are retryable (server errors)
    const status = error?.status || error?.response?.status
    if (status >= 500 && status < 600) {
      return true
    }

    // 429 (Too Many Requests) is retryable
    if (status === 429) {
      return true
    }

    // 408 (Request Timeout) is retryable
    if (status === 408) {
      return true
    }

    // 4xx errors (except 429, 408) are not retryable (client errors)
    if (status >= 400 && status < 500) {
      return false
    }

    // Default: retryable for unknown errors
    return true
  }

  /**
   * Get retry delay in milliseconds (exponential backoff)
   */
  static getRetryDelay(attempt: number, baseDelay: number = 1000): number {
    // Exponential backoff: baseDelay * 2^attempt
    // With jitter to prevent thundering herd
    const exponentialDelay = baseDelay * Math.pow(2, attempt)
    const jitter = Math.random() * 0.3 * exponentialDelay // 0-30% jitter
    return Math.min(exponentialDelay + jitter, 30000) // Max 30 seconds
  }

  /**
   * Classify error type
   */
  static classifyError(error: any): {
    type: 'network' | 'server' | 'client' | 'unknown'
    retryable: boolean
    status?: number
  } {
    const status = error?.status || error?.response?.status

    if (!status) {
      // Network error
      if (error?.message?.includes('NetworkError') || 
          error?.message?.includes('Failed to fetch') ||
          error?.message?.includes('timeout')) {
        return { type: 'network', retryable: true }
      }
      return { type: 'unknown', retryable: true }
    }

    if (status >= 500) {
      return { type: 'server', retryable: true, status }
    }

    if (status >= 400) {
      return { 
        type: 'client', 
        retryable: status === 429 || status === 408, 
        status 
      }
    }

    return { type: 'unknown', retryable: false, status }
  }
}

