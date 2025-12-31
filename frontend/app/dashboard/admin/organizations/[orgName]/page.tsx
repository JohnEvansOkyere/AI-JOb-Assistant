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
import { Building2, Users, FileText, DollarSign, TrendingUp, AlertTriangle, CheckCircle, Settings, Pause, Play, XCircle, CreditCard, BarChart3, FileText as NotesIcon, Filter, RefreshCw } from 'lucide-react'
import { LineChart, BarChart } from '@/components/ui/SimpleChart'
import { StatusChangeModal } from '@/components/admin/StatusChangeModal'
import { PlanChangeModal } from '@/components/admin/PlanChangeModal'
import { UsageLimitsModal } from '@/components/admin/UsageLimitsModal'
import { AdminNotesModal } from '@/components/admin/AdminNotesModal'

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
  settings?: {
    subscription_plan?: string
    status?: string
    monthly_interview_limit?: number | null
    monthly_cost_limit_usd?: number | null
    daily_cost_limit_usd?: number | null
    billing_email?: string
    admin_notes?: string
  }
}

interface CostBreakdown {
  organization: string
  total_cost: number
  breakdown: Array<{
    name: string
    cost: number
    count: number
    tokens: number
  }>
  summary: {
    total_requests: number
    total_tokens: number
    period: {
      start: string
      end: string
    }
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
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  
  // Modal states
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [showPlanModal, setShowPlanModal] = useState(false)
  const [showLimitsModal, setShowLimitsModal] = useState(false)
  const [showNotesModal, setShowNotesModal] = useState(false)
  
  // Cost breakdown states
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown | null>(null)
  const [breakdownLoading, setBreakdownLoading] = useState(false)
  const [breakdownGroupBy, setBreakdownGroupBy] = useState<'feature' | 'provider' | 'user' | 'day' | 'month'>('feature')

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

  const handleSuccess = () => {
    setSuccessMessage('Settings updated successfully')
    setTimeout(() => setSuccessMessage(null), 5000)
    loadDetail()
    loadCostBreakdown()
  }
  
  const loadCostBreakdown = async () => {
    try {
      setBreakdownLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      // Calculate date range (last 30 days)
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - 30)
      
      // Format dates for API (ISO format)
      const startDateStr = startDate.toISOString().split('T')[0] + 'T00:00:00Z'
      const endDateStr = endDate.toISOString().split('T')[0] + 'T23:59:59Z'
      
      const response = await apiClient.get<CostBreakdown>(
        `/admin/costs/organizations/${encodeURIComponent(orgName)}?group_by=${breakdownGroupBy}&start_date=${encodeURIComponent(startDateStr)}&end_date=${encodeURIComponent(endDateStr)}`
      )
      
      if (response.success && response.data) {
        setCostBreakdown(response.data)
      }
    } catch (err: any) {
      console.error('Error loading cost breakdown:', err)
      // Don't show error to user, just log it
    } finally {
      setBreakdownLoading(false)
    }
  }
  
  useEffect(() => {
    if (detail && isAuthenticated) {
      loadCostBreakdown()
    }
  }, [detail, breakdownGroupBy, isAuthenticated])

  const getStatusBadge = (status?: string) => {
    const statusColor = {
      'active': 'bg-green-100 text-green-800 border-green-200',
      'paused': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'suspended': 'bg-red-100 text-red-800 border-red-200',
      'trial': 'bg-blue-100 text-blue-800 border-blue-200',
    }
    const statusClass = statusColor[status as keyof typeof statusColor] || statusColor['active']
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusClass}`}>
        {status === 'active' && <CheckCircle className="w-3 h-3 mr-1" />}
        {status === 'paused' && <Pause className="w-3 h-3 mr-1" />}
        {status === 'suspended' && <XCircle className="w-3 h-3 mr-1" />}
        {status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Active'}
      </span>
    )
  }

  const getPlanBadge = (plan?: string) => {
    const planColors = {
      'free': 'bg-gray-100 text-gray-800',
      'starter': 'bg-blue-100 text-blue-800',
      'professional': 'bg-purple-100 text-purple-800',
      'enterprise': 'bg-indigo-100 text-indigo-800',
      'custom': 'bg-pink-100 text-pink-800',
    }
    const planClass = planColors[plan as keyof typeof planColors] || planColors['free']
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${planClass}`}>
        {plan ? plan.charAt(0).toUpperCase() + plan.slice(1) : 'Free'}
      </span>
    )
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

        {successMessage && (
          <Card>
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
              {successMessage}
            </div>
          </Card>
        )}

        {/* Organization Settings & Admin Controls */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Organization Settings
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <div className="flex items-center gap-3">
                {getStatusBadge(detail.settings?.status)}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowStatusModal(true)}
                >
                  Change
                </Button>
              </div>
            </div>

            {/* Subscription Plan */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Subscription Plan</label>
              <div className="flex items-center gap-3">
                {getPlanBadge(detail.settings?.subscription_plan)}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowPlanModal(true)}
                >
                  Change
                </Button>
              </div>
            </div>

            {/* Usage Limits with Progress Indicators */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Usage Limits</label>
              <div className="space-y-3 text-sm">
                {/* Monthly Interviews */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-600">Monthly Interviews</span>
                    <span className="font-semibold text-gray-900">
                      {detail.usage.total_interviews}
                      {detail.settings?.monthly_interview_limit ? ` / ${detail.settings.monthly_interview_limit}` : ' (Unlimited)'}
                    </span>
                  </div>
                  {detail.settings?.monthly_interview_limit && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          (detail.usage.total_interviews / detail.settings.monthly_interview_limit) >= 0.9
                            ? 'bg-red-500'
                            : (detail.usage.total_interviews / detail.settings.monthly_interview_limit) >= 0.75
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{
                          width: `${Math.min((detail.usage.total_interviews / detail.settings.monthly_interview_limit) * 100, 100)}%`
                        }}
                      />
                    </div>
                  )}
                </div>

                {/* Monthly Cost */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-600">Monthly Cost</span>
                    <span className="font-semibold text-gray-900">
                      {formatCurrency(detail.ai_costs.total_cost_usd)}
                      {detail.settings?.monthly_cost_limit_usd ? ` / ${formatCurrency(detail.settings.monthly_cost_limit_usd)}` : ' (Unlimited)'}
                    </span>
                  </div>
                  {detail.settings?.monthly_cost_limit_usd && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          (detail.ai_costs.total_cost_usd / detail.settings.monthly_cost_limit_usd) >= 0.9
                            ? 'bg-red-500'
                            : (detail.ai_costs.total_cost_usd / detail.settings.monthly_cost_limit_usd) >= 0.75
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{
                          width: `${Math.min((detail.ai_costs.total_cost_usd / detail.settings.monthly_cost_limit_usd) * 100, 100)}%`
                        }}
                      />
                    </div>
                  )}
                </div>

                {/* Daily Cost (would need daily cost calculation, showing placeholder for now) */}
                {detail.settings?.daily_cost_limit_usd && (
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-gray-600">Daily Cost Limit</span>
                      <span className="font-semibold text-gray-900">
                        {formatCurrency(detail.settings.daily_cost_limit_usd)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowLimitsModal(true)}
                className="mt-3"
              >
                Manage Limits
              </Button>
            </div>

            {/* Admin Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Admin Notes</label>
              <div className="text-sm text-gray-600 mb-2 min-h-[40px] p-2 bg-gray-50 rounded border border-gray-200">
                {detail.settings?.admin_notes || <span className="text-gray-400 italic">No notes</span>}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowNotesModal(true)}
              >
                {detail.settings?.admin_notes ? 'Edit Notes' : 'Add Notes'}
              </Button>
            </div>
          </div>
        </Card>

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

        {/* Detailed Cost Breakdown */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Detailed Cost Breakdown</h2>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={breakdownGroupBy}
                onChange={(e) => setBreakdownGroupBy(e.target.value as any)}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="feature">By Feature</option>
                <option value="provider">By Provider</option>
                <option value="user">By User</option>
                <option value="day">By Day</option>
                <option value="month">By Month</option>
              </select>
              <Button
                variant="ghost"
                size="sm"
                onClick={loadCostBreakdown}
                disabled={breakdownLoading}
              >
                <RefreshCw className={`w-4 h-4 ${breakdownLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
          
          {breakdownLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-600">Loading breakdown...</p>
            </div>
          ) : costBreakdown && costBreakdown.breakdown.length > 0 ? (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="text-sm text-gray-500">Total Cost</div>
                  <div className="text-xl font-bold text-gray-900">{formatCurrency(costBreakdown.total_cost)}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Total Requests</div>
                  <div className="text-xl font-bold text-gray-900">{costBreakdown.summary.total_requests.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Total Tokens</div>
                  <div className="text-xl font-bold text-gray-900">{costBreakdown.summary.total_tokens.toLocaleString()}</div>
                </div>
              </div>

              {/* Breakdown Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {breakdownGroupBy === 'feature' ? 'Feature' : 
                         breakdownGroupBy === 'provider' ? 'Provider' : 
                         breakdownGroupBy === 'user' ? 'User' : 
                         breakdownGroupBy === 'day' ? 'Date' : 'Month'}
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cost
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Requests
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tokens
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Cost/Request
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {costBreakdown.breakdown.map((item, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {breakdownGroupBy === 'feature' 
                              ? item.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                              : item.name}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                          {formatCurrency(item.cost)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                          {item.count.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                          {item.tokens.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                          {item.count > 0 ? formatCurrency(item.cost / item.count) : '$0.00'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Chart */}
              <div className="mt-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Cost Distribution</h3>
                <BarChart
                  data={costBreakdown.breakdown.slice(0, 10).map(item => ({
                    label: breakdownGroupBy === 'feature' 
                      ? item.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                      : item.name,
                    value: item.cost,
                  }))}
                />
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No cost breakdown data available for the selected period</p>
          )}
        </Card>

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

        {/* Admin Control Modals */}
        <StatusChangeModal
          isOpen={showStatusModal}
          onClose={() => setShowStatusModal(false)}
          currentStatus={detail.settings?.status}
          orgName={detail.org_name}
          onSuccess={handleSuccess}
        />

        <PlanChangeModal
          isOpen={showPlanModal}
          onClose={() => setShowPlanModal(false)}
          currentPlan={detail.settings?.subscription_plan}
          orgName={detail.org_name}
          onSuccess={handleSuccess}
        />

        <UsageLimitsModal
          isOpen={showLimitsModal}
          onClose={() => setShowLimitsModal(false)}
          orgName={detail.org_name}
          currentLimits={{
            monthly_interview_limit: detail.settings?.monthly_interview_limit,
            monthly_cost_limit_usd: detail.settings?.monthly_cost_limit_usd,
            daily_cost_limit_usd: detail.settings?.daily_cost_limit_usd,
          }}
          onSuccess={handleSuccess}
        />

        <AdminNotesModal
          isOpen={showNotesModal}
          onClose={() => setShowNotesModal(false)}
          orgName={detail.org_name}
          currentNotes={detail.settings?.admin_notes}
          onSuccess={handleSuccess}
        />
      </div>
    </DashboardLayout>
  )
}

