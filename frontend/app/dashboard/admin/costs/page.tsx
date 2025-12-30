/**
 * Admin Costs Page
 * Cost monitoring and analytics
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { apiClient } from '@/lib/api/client'
import { DollarSign, TrendingUp, Building2 } from 'lucide-react'
import { LineChart, BarChart } from '@/components/ui/SimpleChart'

interface CostMonitoring {
  period: {
    start_date: string
    end_date: string
  }
  daily_costs: Record<string, number>
  monthly_costs: Record<string, number>
  cost_by_feature: Record<string, number>
  top_organizations: Array<{
    org_name: string
    cost_usd: number
  }>
}

export default function AdminCostsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [costData, setCostData] = useState<CostMonitoring | null>(null)

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
  }, [isAuthenticated, authLoading, router, user])

  const loadCostData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.get<CostMonitoring>('/admin/costs?group_by=day')
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
      maximumFractionDigits: 2,
    }).format(amount)
  }

  const totalCost = costData
    ? Object.values(costData.daily_costs).reduce((sum, cost) => sum + cost, 0)
    : 0

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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cost Monitoring</h1>
            <p className="text-gray-600 mt-1">
              Period: {new Date(costData.period.start_date).toLocaleDateString()} - {new Date(costData.period.end_date).toLocaleDateString()}
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

        {/* Summary Stat */}
        <StatCard
          title="Total Cost"
          value={formatCurrency(totalCost)}
          icon={<DollarSign className="w-6 h-6" />}
        />

        {/* Daily Costs Chart */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Costs</h2>
          {Object.keys(costData.daily_costs).length > 0 ? (
              <LineChart
                data={Object.entries(costData.daily_costs)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .map(([date, cost]) => ({
                    label: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                    value: cost,
                  }))}
              />
          ) : (
            <p className="text-gray-500">No cost data available</p>
          )}
        </Card>

        {/* Cost Breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Feature</h2>
            {Object.keys(costData.cost_by_feature).length > 0 ? (
              <BarChart
                data={Object.entries(costData.cost_by_feature)
                  .sort(([, a], [, b]) => b - a)
                  .map(([key, value]) => ({
                    label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    value: value,
                  }))}
              />
            ) : (
              <p className="text-gray-500">No cost data available</p>
            )}
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Organizations by Cost</h2>
            {costData.top_organizations.length > 0 ? (
              <div className="space-y-3">
                {costData.top_organizations.map((org, index) => (
                  <div key={org.org_name} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold text-sm">
                        {index + 1}
                      </div>
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-900">{org.org_name}</span>
                      </div>
                    </div>
                    <span className="font-semibold text-gray-900">{formatCurrency(org.cost_usd)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No organization cost data available</p>
            )}
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}

