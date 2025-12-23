/**
 * API Client
 * HTTP client for backend API calls with retry logic and timeout handling
 */

import { ApiErrorHandler } from './error-handler'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
// Increase default timeout to better support long-running operations like CV screening
const DEFAULT_TIMEOUT = 60000 // 60 seconds
// Slightly reduce retries so we don't wait excessively long on repeated timeouts
const DEFAULT_MAX_RETRIES = 2
const DEFAULT_RETRY_DELAY = 1000 // 1 second base delay

export interface ApiResponse<T> {
  success: boolean
  message: string
  data?: T
}

export interface ApiClientOptions {
  timeout?: number
  maxRetries?: number
  retryDelay?: number
  retryableStatusCodes?: number[]
}

export class ApiClient {
  private baseUrl: string
  private token: string | null = null
  private timeout: number
  private maxRetries: number
  private retryDelay: number

  constructor(baseUrl: string = API_URL, options: ApiClientOptions = {}) {
    this.baseUrl = baseUrl
    this.timeout = options.timeout || DEFAULT_TIMEOUT
    this.maxRetries = options.maxRetries || DEFAULT_MAX_RETRIES
    this.retryDelay = options.retryDelay || DEFAULT_RETRY_DELAY
  }

  setToken(token: string | null) {
    this.token = token
  }

  /**
   * Create a timeout promise that rejects after specified time
   */
  private createTimeoutPromise(timeoutMs: number): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Request timeout after ${timeoutMs}ms`))
      }, timeoutMs)
    })
  }

  /**
   * Make request with retry logic and timeout
   */
  private async requestWithRetry<T>(
    endpoint: string,
    options: RequestInit = {},
    attempt: number = 0
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    }

    // Only set JSON content type when we're not sending FormData and the caller
    // hasn't provided an explicit Content-Type header.
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
    if (!isFormData && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    try {
      // Create timeout promise
      const timeoutPromise = this.createTimeoutPromise(this.timeout)

      // Create fetch promise
      const fetchPromise = fetch(url, {
        ...options,
        headers,
      })

      // Race between fetch and timeout
      const response = await Promise.race([fetchPromise, timeoutPromise])

      if (!response.ok) {
        let error: any
        try {
          error = await response.json()
        } catch {
          error = { 
            message: `HTTP error! status: ${response.status}`,
            detail: `HTTP error! status: ${response.status}`
          }
        }
        
        // Handle different error response formats
        const errorMessage = error.detail || 
          (typeof error.detail === 'object' ? error.detail?.error || error.detail?.message : null) || 
          error.message || 
          `HTTP error! status: ${response.status}`
        
        const apiError: any = new Error(errorMessage)
        apiError.response = error
        apiError.status = response.status
        apiError.code = error.error_code || `HTTP_${response.status}`

        // Check if we should retry
        if (attempt < this.maxRetries && ApiErrorHandler.isRetryable(apiError)) {
          const delay = ApiErrorHandler.getRetryDelay(attempt, this.retryDelay)
          console.log(`Request failed, retrying in ${delay}ms (attempt ${attempt + 1}/${this.maxRetries})...`)
          
          await new Promise(resolve => setTimeout(resolve, delay))
          return this.requestWithRetry<T>(endpoint, options, attempt + 1)
        }

        throw apiError
      }

      return await response.json()
    } catch (error: any) {
      // Handle timeout errors
      if (error?.message?.includes('timeout')) {
        if (attempt < this.maxRetries) {
          const delay = ApiErrorHandler.getRetryDelay(attempt, this.retryDelay)
          console.log(`Request timed out, retrying in ${delay}ms (attempt ${attempt + 1}/${this.maxRetries})...`)
          
          await new Promise(resolve => setTimeout(resolve, delay))
          return this.requestWithRetry<T>(endpoint, options, attempt + 1)
        }
        throw new Error('Request timed out. Please check your connection and try again.')
      }

      // Handle network errors
      if (error?.message?.includes('Failed to fetch') || 
          error?.message?.includes('NetworkError')) {
        if (attempt < this.maxRetries) {
          const delay = ApiErrorHandler.getRetryDelay(attempt, this.retryDelay)
          console.log(`Network error, retrying in ${delay}ms (attempt ${attempt + 1}/${this.maxRetries})...`)
          
          await new Promise(resolve => setTimeout(resolve, delay))
          return this.requestWithRetry<T>(endpoint, options, attempt + 1)
        }
        throw new Error('Network error. Please check your internet connection and try again.')
      }

      // Re-throw if it's already an API error
      if (error.status || error.response) {
        throw error
      }

      // Wrap unknown errors
      console.error('API request failed:', error)
      throw error
    }
  }

  /**
   * Make request (wrapper for backward compatibility)
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    return this.requestWithRetry<T>(endpoint, options)
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    // Uploads use longer timeout (60 seconds) and fewer retries (2)
    const originalTimeout = this.timeout
    const originalMaxRetries = this.maxRetries
    
    this.timeout = 60000 // 60 seconds for uploads
    this.maxRetries = 2 // Fewer retries for uploads (they're expensive)
    
    try {
      return await this.requestWithRetry<T>(endpoint, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type for FormData - browser will set it with boundary
      })
    } finally {
      // Restore original settings
      this.timeout = originalTimeout
      this.maxRetries = originalMaxRetries
    }
  }
}

export const apiClient = new ApiClient()

