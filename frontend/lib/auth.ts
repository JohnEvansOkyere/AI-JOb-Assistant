/**
 * Authentication Utilities
 * Helper functions for authentication
 */

import { supabase } from './supabase/client'
import { apiClient } from './api/client'

export interface User {
  id: string
  email: string
  full_name?: string
  company_name?: string
  is_admin?: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
  company_name?: string
  subscription_plan?: string
}

export async function login(credentials: LoginCredentials) {
  try {
    const response = await apiClient.post<{ access_token: string; token_type: string }>(
      '/auth/login',
      credentials
    )

    if (response.success && response.data) {
      // Store token in localStorage
      localStorage.setItem('auth_token', response.data.access_token)
      apiClient.setToken(response.data.access_token)
      
      return { success: true, token: response.data.access_token }
    }

    throw new Error(response.message || 'Login failed')
  } catch (error: any) {
    console.error('Login error:', error)
    return { success: false, error: error.message || 'Login failed' }
  }
}

export async function register(data: RegisterData) {
  try {
    const response = await apiClient.post<User>('/auth/register', data)

    if (response.success) {
      // Don't auto-login - user needs to verify email first
      return { success: true, data: response.data, requiresVerification: true }
    }

    throw new Error(response.message || 'Registration failed')
  } catch (error: any) {
    console.error('Registration error:', error)
    return { success: false, error: error.message || 'Registration failed' }
  }
}

export async function verifyEmail(code: string, email?: string) {
  try {
    const token = localStorage.getItem('auth_token')
    const payload: { code: string; email?: string } = { code }
    
    // Include email if provided (for unauthenticated verification)
    if (email) {
      payload.email = email
    }
    
    // Try with token if available, otherwise use email
    if (token) {
      apiClient.setToken(token)
    } else if (!email) {
      throw new Error('Email is required for verification')
    }
    
    const response = await apiClient.post<{ access_token: string; token_type: string }>(
      '/auth/verify-email',
      payload
    )

    if (response.success && response.data) {
      // Store token and update API client
      localStorage.setItem('auth_token', response.data.access_token)
      apiClient.setToken(response.data.access_token)
      
      return { success: true, token: response.data.access_token }
    }

    throw new Error(response.message || 'Verification failed')
  } catch (error: any) {
    console.error('Email verification error:', error)
    return { success: false, error: error.message || 'Verification failed' }
  }
}

export async function resendVerificationCode(email?: string) {
  try {
    const token = localStorage.getItem('auth_token')
    const payload: { email?: string } = {}
    
    // Include email if provided (for unauthenticated resend)
    if (email) {
      payload.email = email
    }
    
    // Try with token if available, otherwise use email
    if (token) {
      apiClient.setToken(token)
    } else if (!email) {
      throw new Error('Email is required for resending verification code')
    }
    
    const response = await apiClient.post('/auth/resend-verification', payload)

    if (response.success) {
      return { success: true, message: response.message || 'Verification code sent' }
    }

    throw new Error(response.message || 'Failed to resend code')
  } catch (error: any) {
    console.error('Resend verification error:', error)
    return { success: false, error: error.message || 'Failed to resend verification code' }
  }
}

export async function logout() {
  try {
    const token = localStorage.getItem('auth_token')
    if (token) {
      apiClient.setToken(token)
      await apiClient.post('/auth/logout')
    }
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    localStorage.removeItem('auth_token')
    apiClient.setToken(null)
    await supabase.auth.signOut()
  }
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const token = localStorage.getItem('auth_token')
    if (!token) return null

    apiClient.setToken(token)
    const response = await apiClient.get<User>('/auth/me')

    if (response.success && response.data) {
      return response.data
    }

    return null
  } catch (error) {
    console.error('Get current user error:', error)
    return null
  }
}

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

export function isAuthenticated(): boolean {
  return getAuthToken() !== null
}

