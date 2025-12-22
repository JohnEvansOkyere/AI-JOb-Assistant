'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { apiClient } from '@/lib/api/client'
import { useAuth } from '@/hooks/useAuth'

export interface BrandingSettings {
  company_name?: string
  company_type?: string
  industry?: string
  company_size?: string
  headquarters_location?: string
  company_description?: string
  mission_statement?: string
  values_statement?: string
  company_website?: string
  company_address?: string
  company_phone?: string
  company_email?: string
  hiring_email?: string
  default_timezone?: string
  working_model?: string
  linkedin_url?: string
  twitter_url?: string
  facebook_url?: string
  instagram_url?: string
  careers_page_url?: string
  company_logo_url?: string
}

interface BrandingContextValue {
  branding: BrandingSettings | null
  loading: boolean
}

const BrandingContext = createContext<BrandingContextValue | undefined>(undefined)

export function BrandingProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [branding, setBranding] = useState<BrandingSettings | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const loadBranding = async () => {
      try {
        if (!isAuthenticated) {
          setBranding(null)
          return
        }
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
        if (token) {
          apiClient.setToken(token)
        }
        const response = await apiClient.get<any>('/branding/')
        if (response.success && response.data) {
          const data = response.data?.data || response.data
          setBranding(data || null)
        }
      } catch (e) {
        console.error('Failed to load branding settings', e)
      } finally {
        setLoading(false)
      }
    }

    if (!authLoading) {
      loadBranding()
    }
  }, [isAuthenticated, authLoading])

  return (
    <BrandingContext.Provider value={{ branding, loading }}>
      {children}
    </BrandingContext.Provider>
  )
}

export function useBranding() {
  const ctx = useContext(BrandingContext)
  if (!ctx) {
    throw new Error('useBranding must be used within a BrandingProvider')
  }
  return ctx
}


