/**
 * Admin Costs Page
 * Enhanced cost monitoring and analytics dashboard
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/lib/api/client'
import { 
  DollarSign, 
  TrendingUp, 
  Building2, 
  Users, 
  Activity,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Calendar,
  Download,
  Filter
} from 'lucide-react'
import { LineChart, BarChart } from '@/components/ui/SimpleChart'

interface CostMonitoring {
  period: {
    start_date: string
    end_date: string
    days: number
  }
  summary: {
    total_cost_usd: number
    total_requests: number
    total_tokens: number
    avg_daily_cost_usd: number
    avg_cost_per_request_usd: number
    monthly_projection_usd: number
    success_rate_percent: number
    successful_requests: number
    failed_requests: number
  }
  daily_costs: Record<string, number>
  monthly_costs: Record<string, number>
  cost_by_feature: Record<string, {
    cost_usd: number
    request_count: number
    avg_cost_per_request: number
  }>
  cost_by_provider: Record<string, {
    cost_usd: number
    request_count: number
    tokens: number
    avg_cost_per_request: number
  }>
  top_organizations: Array<{
    org_name: string
    cost_usd: number
    request_count: number
    user_count: number
    avg_cost_per_request: number
  }>
  top_users: Array<{
    user_id: string
    user_name: string
    user_email: string
    org_name: string
    cost_usd: number
    request_count: number
    avg_cost_per_request: number
  }>
}

export default function AdminCostsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [costData, setCostData] = useState<CostMonitoring | null>(null)
  const [dateRange, setDateRange] = useState<{start: Date, end: Date}>(() => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 30)
    return { start, end }
  })
  const [groupBy, setGroupBy] = useState<'day' | 'month'>('day')
  const [viewMode, setViewMode] = useState<'organizations' | 'users'>('organizations')

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
      loadCostData()
    }
  }, [isAuthenticated, authLoading, router, user, dateRange, groupBy])

  const loadCostData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const startDateStr = dateRange.start.toISOString().split('T')[0]
      const endDateStr = dateRange.end.toISOString().split('T')[0] + 'T23:59:59'
      
      const response = await apiClient.get<CostMonitoring>(
        `/admin/costs?group_by=${groupBy}&start_date=${encodeURIComponent(startDateStr)}&end_date=${encodeURIComponent(endDateStr)}`
      )
      if (response.success && response.data) {
        setCostData(response.data)
      } else {
        setError(response.message || 'Failed to load cost data')
      }
    } catch (err: any) {
      if (err.message?.includes('403') || err.message?.includes('Admin access required')) {
        setError('Admin access required')
        router.push('/dashboard')
      } else {
        setError(err.message || 'Failed to load cost data')
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
      maximumFractionDigits: 4,
    }).format(amount)
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num)
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading cost data...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated || !costData) {
    return null
  }

  const summary = costData.summary

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Cost Monitoring Dashboard</h1>
            <p className="text-gray-600 mt-1">
              Period: {new Date(costData.period.start_date).toLocaleDateString()} - {new Date(costData.period.end_date).toLocaleDateString()}
              {' '}({costData.period.days} days)
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <input
                type="date"
                value={dateRange.start.toISOString().split('T')[0]}
                onChange={(e) => setDateRange({...dateRange, start: new Date(e.target.value)})}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={dateRange.end.toISOString().split('T')[0]}
                onChange={(e) => setDateRange({...dateRange, end: new Date(e.target.value)})}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm"
              />
            </div>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as 'day' | 'month')}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm"
            >
              <option value="day">By Day</option>
              <option value="month">By Month</option>
            </select>
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
            title="Total Cost"
            value={formatCurrency(summary.total_cost_usd)}
            icon={<DollarSign className="w-6 h-6" />}
            subtitle={`${formatNumber(summary.total_requests)} requests`}
          />
          <StatCard
            title="Avg Daily Cost"
            value={formatCurrency(summary.avg_daily_cost_usd)}
            icon={<TrendingUp className="w-6 h-6" />}
            subtitle={`Projected: ${formatCurrency(summary.monthly_projection_usd)}/mo`}
          />
          <StatCard
            title="Avg per Request"
            value={formatCurrency(summary.avg_cost_per_request_usd)}
            icon={<Activity className="w-6 h-6" />}
            subtitle={`${formatNumber(summary.total_tokens)} tokens`}
          />
          <StatCard
            title="Success Rate"
            value={`${summary.success_rate_percent.toFixed(1)}%`}
            icon={summary.success_rate_percent >= 95 ? <CheckCircle className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
            subtitle={`${summary.failed_requests} failed / ${summary.successful_requests} success`}
          />
        </div>

        {/* Daily/Monthly Costs Chart */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Cost Trends - {groupBy === 'day' ? 'Daily' : 'Monthly'}
            </h2>
          </div>
          {Object.keys(costData.daily_costs).length > 0 ? (
            <LineChart
              data={Object.entries(groupBy === 'day' ? costData.daily_costs : costData.monthly_costs)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([date, cost]) => ({
                  label: groupBy === 'day' 
                    ? new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                    : new Date(date + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                  value: cost,
                }))}
            />
          ) : (
            <p className="text-gray-500 text-center py-8">No cost data available for this period</p>
          )}
        </Card>

        {/* Cost Breakdowns by Feature and Provider */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Feature</h2>
            {Object.keys(costData.cost_by_feature).length > 0 ? (
              <div className="space-y-4">
                <BarChart
                  data={Object.entries(costData.cost_by_feature)
                    .sort(([, a], [, b]) => (b as any).cost_usd - (a as any).cost_usd)
                    .slice(0, 10)
                    .map(([key, data]: [string, any]) => ({
                      label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                      value: data.cost_usd,
                    }))}
                />
                <div className="mt-4 space-y-2">
                  {Object.entries(costData.cost_by_feature)
                    .sort(([, a], [, b]) => (b as any).cost_usd - (a as any).cost_usd)
                    .map(([feature, data]: [string, any]) => (
                      <div key={feature} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                        <div>
                          <div className="font-medium text-gray-900">
                            {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatNumber(data.request_count)} requests · Avg: {formatCurrency(data.avg_cost_per_request)}
                          </div>
                        </div>
                        <div className="font-semibold text-gray-900">{formatCurrency(data.cost_usd)}</div>
                      </div>
                    ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No cost data available</p>
            )}
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Provider</h2>
            {Object.keys(costData.cost_by_provider).length > 0 ? (
              <div className="space-y-4">
                <BarChart
                  data={Object.entries(costData.cost_by_provider)
                    .sort(([, a], [, b]) => (b as any).cost_usd - (a as any).cost_usd)
                    .map(([key, data]: [string, any]) => ({
                      label: key.toUpperCase(),
                      value: data.cost_usd,
                    }))}
                />
                <div className="mt-4 space-y-2">
                  {Object.entries(costData.cost_by_provider)
                    .sort(([, a], [, b]) => (b as any).cost_usd - (a as any).cost_usd)
                    .map(([provider, data]: [string, any]) => (
                      <div key={provider} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                        <div>
                          <div className="font-medium text-gray-900">{provider.toUpperCase()}</div>
                          <div className="text-xs text-gray-500">
                            {formatNumber(data.request_count)} requests
                            {data.tokens > 0 && ` · ${formatNumber(data.tokens)} tokens`}
                            {' '}· Avg: {formatCurrency(data.avg_cost_per_request)}
                          </div>
                        </div>
                        <div className="font-semibold text-gray-900">{formatCurrency(data.cost_usd)}</div>
                      </div>
                    ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No cost data available</p>
            )}
          </Card>
        </div>

        {/* Clients/Users Breakdown */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Cost by {viewMode === 'organizations' ? 'Organization' : 'User'}
            </h2>
            <div className="flex items-center gap-2">
              <Button
                variant={viewMode === 'organizations' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setViewMode('organizations')}
              >
                <Building2 className="w-4 h-4 mr-1" />
                Organizations
              </Button>
              <Button
                variant={viewMode === 'users' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setViewMode('users')}
              >
                <Users className="w-4 h-4 mr-1" />
                Users
              </Button>
            </div>
          </div>

          {viewMode === 'organizations' ? (
            costData.top_organizations.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Organization</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Users</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg/Request</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Cost</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">% of Total</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {costData.top_organizations.map((org, index) => {
                      const percentage = (org.cost_usd / summary.total_cost_usd * 100).toFixed(1)
                      return (
                        <tr key={org.org_name} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold text-sm">
                              {index + 1}
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4 text-gray-400" />
                              <span className="font-medium text-gray-900">{org.org_name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                            {org.user_count}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                            {formatNumber(org.request_count)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                            {formatCurrency(org.avg_cost_per_request)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                            {formatCurrency(org.cost_usd)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                            {percentage}%
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No organization cost data available</p>
            )
          ) : (
            costData.top_users.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Organization</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg/Request</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Cost</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">% of Total</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {costData.top_users.map((user, index) => {
                      const percentage = (user.cost_usd / summary.total_cost_usd * 100).toFixed(1)
                      return (
                        <tr key={user.user_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold text-sm">
                              {index + 1}
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex flex-col">
                              <span className="font-medium text-gray-900">{user.user_name}</span>
                              <span className="text-xs text-gray-500">{user.user_email}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-600">{user.org_name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                            {formatNumber(user.request_count)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                            {formatCurrency(user.avg_cost_per_request)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-semibold text-gray-900">
                            {formatCurrency(user.cost_usd)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                            {percentage}%
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No user cost data available</p>
            )
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}
