/**
 * useAuth Hook
 * React hook for authentication state management
 */

'use client'

import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { User, login, register, logout, getCurrentUser, isAuthenticated } from '@/lib/auth'
import { apiClient } from '@/lib/api/client'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (data: { email: string; password: string; full_name?: string; company_name?: string }) => Promise<{ success: boolean; error?: string }>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Initialize auth token
    const token = localStorage.getItem('auth_token')
    if (token) {
      apiClient.setToken(token)
    }

    // Load user on mount
    loadUser()
  }, [])

  const loadUser = async () => {
    try {
      if (isAuthenticated()) {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
      }
    } catch (error) {
      console.error('Failed to load user:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (email: string, password: string) => {
    const result = await login({ email, password })
    if (result.success) {
      await loadUser()
    }
    return result
  }

  const handleRegister = async (data: { email: string; password: string; full_name?: string; company_name?: string }) => {
    const result = await register(data)
    if (result.success) {
      await loadUser()
    }
    return result
  }

  const handleLogout = async () => {
    await logout()
    setUser(null)
  }

  const refreshUser = async () => {
    await loadUser()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

