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
      // Auto-login after registration
      return await login({ email: data.email, password: data.password })
    }

    throw new Error(response.message || 'Registration failed')
  } catch (error: any) {
    console.error('Registration error:', error)
    return { success: false, error: error.message || 'Registration failed' }
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

