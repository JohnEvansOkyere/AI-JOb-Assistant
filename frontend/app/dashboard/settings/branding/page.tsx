/**
 * Branding Management Page
 * Upload logo, set colors, customize letterhead
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { ArrowLeft, Upload, Save, Eye } from 'lucide-react'

export default function BrandingPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [loading, setLoading] = useState(false)
  const [loadingBranding, setLoadingBranding] = useState(true)
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string>('')
  const [formData, setFormData] = useState({
    company_name: '',
    primary_color: '#2563eb',
    secondary_color: '#1e40af',
    company_website: '',
    company_address: '',
    company_phone: '',
    company_email: '',
    sender_name: '',
    sender_title: '',
    email_signature: '',
    letterhead_background_color: '#ffffff',
  })

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadBranding()
    }
  }, [isAuthenticated, authLoading, router])

  const loadBranding = async () => {
    try {
      setLoadingBranding(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any>('/branding/')
      if (response.success && response.data) {
        // Handle both response.data (direct) and response.data.data (nested)
        const branding = response.data?.data || response.data || {}
        setFormData({
          company_name: branding.company_name || '',
          primary_color: branding.primary_color || '#2563eb',
          secondary_color: branding.secondary_color || '#1e40af',
          company_website: branding.company_website || '',
          company_address: branding.company_address || '',
          company_phone: branding.company_phone || '',
          company_email: branding.company_email || '',
          sender_name: branding.sender_name || '',
          sender_title: branding.sender_title || '',
          email_signature: branding.email_signature || '',
          letterhead_background_color: branding.letterhead_background_color || '#ffffff',
        })
        if (branding.company_logo_url) {
          setLogoPreview(branding.company_logo_url)
        }
      }
    } catch (err: any) {
      console.error('Error loading branding:', err)
    } finally {
      setLoadingBranding(false)
    }
  }

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setLogoFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setLogoPreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSave = async () => {
    if (!formData.company_name) {
      alert('Company name is required')
      return
    }

    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const formDataToSend = new FormData()
      Object.entries(formData).forEach(([key, value]) => {
        if (value) {
          formDataToSend.append(key, value)
        }
      })
      formDataToSend.append('is_default', 'true')

      if (logoFile) {
        formDataToSend.append('logo_file', logoFile)
      }

      const response = await apiClient.upload('/branding/', formDataToSend)

      if (response.success) {
        alert('Branding saved successfully!')
        loadBranding()
      } else {
        alert('Failed to save branding: ' + response.message)
      }
    } catch (err: any) {
      console.error('Error saving branding:', err)
      alert('Error saving branding: ' + (err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loadingBranding) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard/emails')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Company Branding</h1>
              <p className="text-gray-600 mt-1">Customize your email letterhead and branding</p>
            </div>
          </div>
          <Button
            variant="primary"
            onClick={handleSave}
            loading={loading}
          >
            <Save className="w-4 h-4 mr-2" />
            Save Branding
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <div className="p-6 space-y-4">
                <h2 className="font-semibold text-gray-900">Company Information</h2>
                <Input
                  label="Company Name *"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  required
                />
                <Input
                  label="Company Website"
                  type="url"
                  value={formData.company_website}
                  onChange={(e) => setFormData({ ...formData, company_website: e.target.value })}
                  placeholder="https://example.com"
                />
                <Input
                  label="Company Address"
                  value={formData.company_address}
                  onChange={(e) => setFormData({ ...formData, company_address: e.target.value })}
                />
                <Input
                  label="Company Phone"
                  value={formData.company_phone}
                  onChange={(e) => setFormData({ ...formData, company_phone: e.target.value })}
                />
                <Input
                  label="Company Email"
                  type="email"
                  value={formData.company_email}
                  onChange={(e) => setFormData({ ...formData, company_email: e.target.value })}
                />
              </div>
            </Card>

            <Card>
              <div className="p-6 space-y-4">
                <h2 className="font-semibold text-gray-900">Branding Colors</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Primary Color
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={formData.primary_color}
                        onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                        className="w-16 h-10 rounded border border-gray-300"
                      />
                      <Input
                        value={formData.primary_color}
                        onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                        placeholder="#2563eb"
                        className="flex-1"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Secondary Color
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={formData.secondary_color}
                        onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                        className="w-16 h-10 rounded border border-gray-300"
                      />
                      <Input
                        value={formData.secondary_color}
                        onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                        placeholder="#1e40af"
                        className="flex-1"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-6 space-y-4">
                <h2 className="font-semibold text-gray-900">Sender Information</h2>
                <Input
                  label="Sender Name"
                  value={formData.sender_name}
                  onChange={(e) => setFormData({ ...formData, sender_name: e.target.value })}
                  placeholder="Jane Recruiter"
                />
                <Input
                  label="Sender Title"
                  value={formData.sender_title}
                  onChange={(e) => setFormData({ ...formData, sender_title: e.target.value })}
                  placeholder="Senior Recruiter"
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Signature (HTML)
                  </label>
                  <textarea
                    value={formData.email_signature}
                    onChange={(e) => setFormData({ ...formData, email_signature: e.target.value })}
                    placeholder="<p>Best regards,<br>Jane</p>"
                    className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <div className="p-6 space-y-4">
                <h2 className="font-semibold text-gray-900">Company Logo</h2>
                {logoPreview && (
                  <div className="mb-4">
                    <img
                      src={logoPreview}
                      alt="Logo preview"
                      className="w-full h-32 object-contain border border-gray-200 rounded-lg p-4 bg-white"
                    />
                  </div>
                )}
                <label className="block">
                  <span className="sr-only">Upload logo</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleLogoChange}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                  />
                </label>
                <p className="text-xs text-gray-500">
                  PNG, JPG, or SVG. Max 5MB. Logo will appear in email header.
                </p>
              </div>
            </Card>

            <Card>
              <div className="p-6">
                <h2 className="font-semibold text-gray-900 mb-4">Preview</h2>
                <div
                  className="border border-gray-200 rounded-lg p-4 bg-white"
                  style={{ backgroundColor: formData.letterhead_background_color }}
                >
                  <div
                    className="p-4 rounded mb-4 text-white text-center"
                    style={{ backgroundColor: formData.primary_color }}
                  >
                    {logoPreview && (
                      <img
                        src={logoPreview}
                        alt="Logo"
                        className="h-8 mx-auto mb-2"
                      />
                    )}
                    <h3 className="font-bold">{formData.company_name || 'Company Name'}</h3>
                  </div>
                  <div className="bg-white p-4 rounded">
                    <p className="text-sm text-gray-700">Email content will appear here...</p>
                  </div>
                  {formData.email_signature && (
                    <div
                      className="mt-4 p-4 rounded"
                      style={{ backgroundColor: formData.secondary_color + '20' }}
                      dangerouslySetInnerHTML={{ __html: formData.email_signature }}
                    />
                  )}
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

