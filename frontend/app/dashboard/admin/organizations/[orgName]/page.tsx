/**
 * Admin Organization Detail Page
 * Detailed metrics for a specific organization
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { StatCard } from '@/components/ui/StatCard'
import { apiClient } from '@/lib/api/client'
import { Building2, Users, FileText, DollarSign, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import { LineChart, BarChart } from '@/components/ui/SimpleChart'

interface OrganizationDetail {
  org_name: string
  active_users: number
  period: {
    start_date: string
    end_date: string
  }
  usage: {
    total_interviews: number
    completed_interviews: number
    completion_rate: number
  }
  ai_costs: {
    total_cost_usd: number
    by_feature: Record<string, number>
    by_provider: Record<string, number>
  }
  ai_usage: {
    openai_tokens: number
    elevenlabs_characters: number
  }
  system_health: {
    total_requests: number
    failed_requests: number
    error_rate_percent: number
  }
}

export default function AdminOrganizationDetailPage() {
  const router = useRouter()
  const params = useParams()
  const orgName = decodeURIComponent(params.orgName as string)
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [detail, setDetail] = useState<OrganizationDetail | null>(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }
    
    if (!authLoading && isAuthenticated && user && !(user as any).is_admin) {
      router.push('/dashboard')
      return
    }
    
    if (!authLoading && isAuthenticated) {
      loadDetail()
    }
  }, [isAuthenticated, authLoading, router, user, orgName])

  const loadDetail = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.get<OrganizationDetail>(
        `/admin/organizations/${encodeURIComponent(orgName)}`
      )
      if (response.success && response.data) {
        setDetail(response.data)
      } else {
        setError(response.message || 'Failed to load organization details')
      }
    } catch (err: any) {
      if (err.message?.includes('403') || err.message?.includes('Admin access required')) {
        setError('Admin access required')
        router.push('/dashboard')
      } else {
        setError(err.message || 'Failed to load organization details')
      }
    } finally {
      setLoading(false)
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

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading organization details...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated || !detail) {
    return null
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Button variant="outline" size="sm" onClick={() => router.push('/dashboard/admin/organizations')}>
              ← Back to Organizations
            </Button>
            <h1 className="text-2xl font-bold text-gray-900 mt-4 flex items-center gap-2">
              <Building2 className="w-6 h-6" />
              {detail.org_name}
            </h1>
            <p className="text-gray-600 mt-1">
              Period: {new Date(detail.period.start_date).toLocaleDateString()} - {new Date(detail.period.end_date).toLocaleDateString()}
            </p>
          </div>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Active Users"
            value={detail.active_users.toString()}
            icon={<Users className="w-6 h-6" />}
          />
          <StatCard
            title="Completed Interviews"
            value={`${detail.usage.completed_interviews} / ${detail.usage.total_interviews}`}
            icon={<FileText className="w-6 h-6" />}
          />
          <StatCard
            title="Total AI Cost"
            value={formatCurrency(detail.ai_costs.total_cost_usd)}
            icon={<DollarSign className="w-6 h-6" />}
          />
          <StatCard
            title="Error Rate"
            value={`${detail.system_health.error_rate_percent.toFixed(2)}%`}
            icon={detail.system_health.error_rate_percent < 5 ? <CheckCircle className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
          />
        </div>

        {/* Usage Metrics */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Usage Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-500">Interview Completion Rate</div>
              <div className="text-2xl font-bold text-gray-900">{detail.usage.completion_rate.toFixed(1)}%</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">OpenAI Tokens Used</div>
              <div className="text-2xl font-bold text-gray-900">{detail.ai_usage.openai_tokens.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">ElevenLabs Characters</div>
              <div className="text-2xl font-bold text-gray-900">{detail.ai_usage.elevenlabs_characters.toLocaleString()}</div>
            </div>
          </div>
        </Card>

        {/* Cost Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Feature</h2>
            {Object.keys(detail.ai_costs.by_feature).length > 0 ? (
              <BarChart
                data={Object.entries(detail.ai_costs.by_feature).map(([key, value]) => ({
                  label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                  value: value,
                }))}
              />
            ) : (
              <p className="text-gray-500">No cost data available</p>
            )}
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Provider</h2>
            {Object.keys(detail.ai_costs.by_provider).length > 0 ? (
              <BarChart
                data={Object.entries(detail.ai_costs.by_provider).map(([key, value]) => ({
                  label: key,
                  value: value,
                }))}
              />
            ) : (
              <p className="text-gray-500">No cost data available</p>
            )}
          </Card>
        </div>

        {/* System Health */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-500">Total Requests</div>
              <div className="text-2xl font-bold text-gray-900">{detail.system_health.total_requests.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Failed Requests</div>
              <div className="text-2xl font-bold text-red-600">{detail.system_health.failed_requests}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Success Rate</div>
              <div className="text-2xl font-bold text-green-600">
                {(100 - detail.system_health.error_rate_percent).toFixed(2)}%
              </div>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}

