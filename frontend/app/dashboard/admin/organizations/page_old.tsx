/**
 * Admin Organizations Page
 * Overview of all organizations with usage metrics
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/lib/api/client'
import { Building2, Users, FileText, DollarSign, Calendar, ArrowUpDown, Briefcase } from 'lucide-react'

interface Organization {
  org_id: string
  org_name: string
  active_users: number
  jobs_created: number
  interviews_created: number
  interviews_completed: number
  cvs_screened: number
  monthly_ai_cost_usd: number
  cost_per_interview_usd: number
  last_activity: string | null
}

export default function AdminOrganizationsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [sortBy, setSortBy] = useState<string>('last_activity')
  const [sortOrder, setSortOrder] = useState<string>('desc')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }
    
    // Check if user is admin
    if (!authLoading && isAuthenticated && user && !(user as any).is_admin) {
      router.push('/dashboard')
      return
    }
    
    if (!authLoading && isAuthenticated) {
      loadOrganizations()
    }
  }, [isAuthenticated, authLoading, router, user, sortBy, sortOrder])

  const loadOrganizations = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.get<Organization[]>(
        `/admin/organizations?sort_by=${sortBy}&sort_order=${sortOrder}`
      )
      if (response.success && Array.isArray(response.data)) {
        setOrganizations(response.data)
      } else {
        setError(response.message || 'Failed to load organizations')
      }
    } catch (err: any) {
      if (err.message?.includes('403') || err.message?.includes('Admin access required')) {
        setError('Admin access required. You do not have permission to view this page.')
        router.push('/dashboard')
      } else {
        setError(err.message || 'Failed to load organizations')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading organizations...</p>
          </div>
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
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Organizations Overview</h1>
            <p className="text-gray-600 mt-1">Monitor customer usage and AI costs</p>
          </div>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        <Card>
          {organizations.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-2">No organizations found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs font-semibold text-gray-500 uppercase">
                    <th className="py-3 pr-4">
                      <button
                        onClick={() => handleSort('org_name')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Organization
                        <ArrowUpDown className="w-3 h-3" />
                      </button>
                    </th>
                    <th className="py-3 pr-4">
                      <button
                        onClick={() => handleSort('interviews_completed')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Active Users
                      </button>
                    </th>
                    <th className="py-3 pr-4">Interviews</th>
                    <th className="py-3 pr-4">CVs Screened</th>
                    <th className="py-3 pr-4">
                      <button
                        onClick={() => handleSort('monthly_ai_cost_usd')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Monthly AI Cost
                        <ArrowUpDown className="w-3 h-3" />
                      </button>
                    </th>
                    <th className="py-3 pr-4">Cost/Interview</th>
                    <th className="py-3 pr-4">
                      <button
                        onClick={() => handleSort('last_activity')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Last Activity
                        <ArrowUpDown className="w-3 h-3" />
                      </button>
                    </th>
                    <th className="py-3 pr-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {organizations.map((org) => (
                    <tr key={org.org_id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 pr-4">
                        <div className="font-medium text-gray-900 flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-gray-400" />
                          {org.org_name}
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-1 text-gray-700">
                          <Users className="w-4 h-4 text-gray-400" />
                          {org.active_users}
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-gray-700">
                        <div className="flex items-center gap-1">
                          <Briefcase className="w-4 h-4 text-gray-400" />
                          <span className="font-medium">{org.jobs_created || 0}</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-gray-700">
                        <div>
                          <span className="font-medium">{org.interviews_completed}</span>
                          <span className="text-gray-500"> / {org.interviews_created}</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-gray-700">
                        <div className="flex items-center gap-1">
                          <FileText className="w-4 h-4 text-gray-400" />
                          {org.cvs_screened}
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-1 font-medium text-gray-900">
                          <DollarSign className="w-4 h-4 text-green-600" />
                          {formatCurrency(org.monthly_ai_cost_usd)}
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-gray-700">
                        {org.cost_per_interview_usd > 0
                          ? formatCurrency(org.cost_per_interview_usd)
                          : '—'}
                      </td>
                      <td className="py-3 pr-4 text-gray-500 text-xs">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(org.last_activity)}
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/dashboard/admin/organizations/${encodeURIComponent(org.org_name)}`)}
                        >
                          View Details
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}

