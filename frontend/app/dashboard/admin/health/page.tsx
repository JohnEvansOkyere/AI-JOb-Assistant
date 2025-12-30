/**
 * Admin System Health Page
 * System health and performance metrics
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { apiClient } from '@/lib/api/client'
import { Activity, AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface ProviderHealth {
  total_requests: number
  success_rate: number
  error_rate: number
  avg_latency_ms: number
  recent_errors: string[]
}

interface SystemHealth {
  period: {
    start_date: string
    end_date: string
  }
  providers: Record<string, ProviderHealth>
}

export default function AdminHealthPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [healthData, setHealthData] = useState<SystemHealth | null>(null)

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
      loadHealthData()
    }
  }, [isAuthenticated, authLoading, router, user])

  const loadHealthData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.get<SystemHealth>('/admin/system-health')
      if (response.success && response.data) {
        setHealthData(response.data)
      } else {
        setError(response.message || 'Failed to load system health data')
      }
    } catch (err: any) {
      if (err.message?.includes('403') || err.message?.includes('Admin access required')) {
        setError('Admin access required')
        router.push('/dashboard')
      } else {
        setError(err.message || 'Failed to load system health data')
      }
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading system health data...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated || !healthData) {
    return null
  }

  const providers = Object.entries(healthData.providers)
  const totalRequests = providers.reduce((sum, [, stats]) => sum + stats.total_requests, 0)
  const totalErrors = providers.reduce((sum, [, stats]) => sum + (stats.total_requests - (stats.total_requests * stats.success_rate / 100)), 0)
  const avgSuccessRate = providers.length > 0
    ? providers.reduce((sum, [, stats]) => sum + stats.success_rate, 0) / providers.length
    : 0

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
            <p className="text-gray-600 mt-1">
              Period: {new Date(healthData.period.start_date).toLocaleDateString()} - {new Date(healthData.period.end_date).toLocaleDateString()}
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            title="Total Requests"
            value={totalRequests.toLocaleString()}
            icon={<Activity className="w-6 h-6" />}
          />
          <StatCard
            title="Overall Success Rate"
            value={`${avgSuccessRate.toFixed(2)}%`}
            icon={avgSuccessRate > 95 ? <CheckCircle className="w-6 h-6" /> : <AlertCircle className="w-6 h-6" />}
          />
          <StatCard
            title="Total Errors"
            value={Math.round(totalErrors).toLocaleString()}
            icon={<AlertCircle className="w-6 h-6" />}
          />
        </div>

        {/* Provider Health Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {providers.map(([provider, stats]) => (
            <Card key={provider}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 capitalize">{provider}</h2>
                {stats.success_rate > 95 ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-yellow-600" />
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-sm text-gray-500">Total Requests</div>
                  <div className="text-2xl font-bold text-gray-900">{stats.total_requests.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Success Rate</div>
                  <div className={`text-2xl font-bold ${stats.success_rate > 95 ? 'text-green-600' : 'text-yellow-600'}`}>
                    {stats.success_rate.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Error Rate</div>
                  <div className={`text-2xl font-bold ${stats.error_rate > 5 ? 'text-red-600' : 'text-gray-600'}`}>
                    {stats.error_rate.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Avg Latency
                  </div>
                  <div className="text-2xl font-bold text-gray-900">{stats.avg_latency_ms.toFixed(0)}ms</div>
                </div>
              </div>

              {stats.recent_errors.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm font-medium text-gray-700 mb-2">Recent Errors:</div>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {stats.recent_errors.map((error, index) => (
                      <div key={index} className="text-xs text-red-600 bg-red-50 p-2 rounded">
                        {error.substring(0, 200)}{error.length > 200 ? '...' : ''}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>

        {providers.length === 0 && (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600">No health data available for the selected period.</p>
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}

