/**
 * Admin Dashboard Overview
 * Comprehensive monitoring dashboard for system admins
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
  Building2, 
  Users, 
  FileText, 
  DollarSign, 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle,
  Briefcase,
  BarChart3,
  ArrowRight
} from 'lucide-react'
import { LineChart, BarChart } from '@/components/ui/SimpleChart'

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

interface SystemHealth {
  period: {
    start_date: string
    end_date: string
  }
  providers: Record<string, {
    total_requests: number
    success_rate: number
    error_rate: number
    avg_latency_ms: number
    recent_errors: string[]
  }>
}

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

export default function AdminDashboardPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [costData, setCostData] = useState<CostMonitoring | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
      return
    }
    
    if (!authLoading && user && !user.is_admin) {
      router.push('/dashboard')
      return
    }
    
    if (!authLoading && user?.is_admin) {
      loadDashboardData()
    }
  }, [authLoading, user, router])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      // Load all data in parallel
      const [orgsResponse, healthResponse, costsResponse] = await Promise.all([
        apiClient.get<Organization[]>('/admin/organizations'),
        apiClient.get<SystemHealth>('/admin/system-health'),
        apiClient.get<CostMonitoring>('/admin/costs'),
      ])

      if (orgsResponse.success && Array.isArray(orgsResponse.data)) {
        setOrganizations(orgsResponse.data as Organization[])
      }

      if (healthResponse.success && healthResponse.data) {
        setSystemHealth(healthResponse.data)
      }

      if (costsResponse.success && costsResponse.data) {
        setCostData(costsResponse.data)
      }

    } catch (err: any) {
      if (err.message?.includes('403') || err.message?.includes('Admin access required')) {
        setError('Admin access required. You do not have permission to view this page.')
        router.push('/dashboard')
      } else {
        setError(err.message || 'Failed to load dashboard data')
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

  // Calculate summary stats
  const totalOrganizations = organizations.length
  const totalUsers = organizations.reduce((sum, org) => sum + org.active_users, 0)
  const totalJobs = organizations.reduce((sum, org: Organization) => sum + (org.jobs_created || 0), 0)
  const totalInterviewsCompleted = organizations.reduce((sum, org) => sum + org.interviews_completed, 0)
  const totalCost = costData && costData.daily_costs
    ? Object.values(costData.daily_costs).reduce((sum, cost) => sum + cost, 0)
    : organizations.reduce((sum, org) => sum + org.monthly_ai_cost_usd, 0)

  // System health summary
  const totalRequests = systemHealth && systemHealth.providers
    ? Object.values(systemHealth.providers).reduce((sum, p) => sum + p.total_requests, 0)
    : 0
  const avgSuccessRate = systemHealth && systemHealth.providers && Object.keys(systemHealth.providers).length > 0
    ? Object.values(systemHealth.providers).reduce((sum, p) => sum + p.success_rate, 0) / Object.keys(systemHealth.providers).length
    : 0
  const totalErrors = systemHealth && systemHealth.providers
    ? Object.values(systemHealth.providers).reduce((sum, p) => sum + (p.total_requests * p.error_rate / 100), 0)
    : 0

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!user || !user.is_admin) {
    return null
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-600 mt-1">Comprehensive system monitoring and analytics</p>
          </div>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Organizations"
            value={totalOrganizations.toString()}
            icon={<Building2 className="w-6 h-6" />}
          />
          <StatCard
            title="Total Users"
            value={totalUsers.toString()}
            icon={<Users className="w-6 h-6" />}
          />
          <StatCard
            title="Jobs Created"
            value={totalJobs.toString()}
            icon={<Briefcase className="w-6 h-6" />}
          />
          <StatCard
            title="Completed Interviews"
            value={totalInterviewsCompleted.toString()}
            icon={<FileText className="w-6 h-6" />}
          />
        </div>

        {/* AI Usage & Costs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            title="Total AI Cost (30 days)"
            value={formatCurrency(totalCost)}
            icon={<DollarSign className="w-6 h-6" />}
          />
          <StatCard
            title="Total AI Requests"
            value={totalRequests.toLocaleString()}
            icon={<Activity className="w-6 h-6" />}
          />
          <StatCard
            title="Overall Success Rate"
            value={`${avgSuccessRate.toFixed(2)}%`}
            icon={avgSuccessRate > 95 ? <CheckCircle className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
          />
        </div>

        {/* Organizations Overview */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Organizations</h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard/admin/organizations')}
            >
              View All <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
          
          {organizations.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No organizations found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs font-semibold text-gray-500 uppercase">
                    <th className="py-3 pr-4">Organization</th>
                    <th className="py-3 pr-4">Users</th>
                    <th className="py-3 pr-4">Jobs</th>
                    <th className="py-3 pr-4">Interviews</th>
                    <th className="py-3 pr-4">AI Cost</th>
                    <th className="py-3 pr-4">AI Usage</th>
                  </tr>
                </thead>
                <tbody>
                  {organizations.slice(0, 10).map((org) => (
                    <tr key={org.org_id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 pr-4">
                        <div className="font-medium text-gray-900 flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-gray-400" />
                          {org.org_name}
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-gray-700">{org.active_users}</td>
                      <td className="py-3 pr-4 text-gray-700">
                        <span className="font-medium">{org.interviews_created}</span>
                      </td>
                      <td className="py-3 pr-4 text-gray-700">
                        <span className="font-medium">{org.interviews_completed}</span>
                        <span className="text-gray-500"> / {org.interviews_created}</span>
                      </td>
                      <td className="py-3 pr-4">
                        <div className="font-medium text-gray-900">{formatCurrency(org.monthly_ai_cost_usd)}</div>
                      </td>
                      <td className="py-3 pr-4 text-gray-700">
                        {org.cvs_screened} CVs screened
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {organizations.length > 10 && (
                <div className="mt-4 text-center">
                  <Button
                    variant="outline"
                    onClick={() => router.push('/dashboard/admin/organizations')}
                  >
                    View All {organizations.length} Organizations
                  </Button>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Cost Trends */}
        {costData && Object.keys(costData.daily_costs).length > 0 && (
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Daily AI Costs (Last 30 Days)</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/dashboard/admin/costs')}
              >
                View Details <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
            <LineChart
              height={300}
              data={Object.entries(costData.daily_costs)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([date, cost]) => ({
                  label: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                  value: cost,
                }))}
            />
          </Card>
        )}

        {/* System Health Summary */}
        {systemHealth && systemHealth.providers && Object.keys(systemHealth.providers).length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => router.push('/dashboard/admin/health')}
                >
                  View Details <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
              
              <div className="space-y-4">
                {Object.entries(systemHealth.providers).map(([provider, stats]) => (
                  <div key={provider} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${stats.success_rate > 95 ? 'bg-green-500' : stats.success_rate > 80 ? 'bg-yellow-500' : 'bg-red-500'}`} />
                      <span className="font-medium text-gray-900 capitalize">{provider}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-gray-600">{stats.total_requests.toLocaleString()} requests</span>
                      <span className={`font-medium ${stats.success_rate > 95 ? 'text-green-600' : stats.success_rate > 80 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {stats.success_rate.toFixed(1)}% success
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Top Spending Organizations */}
            {costData && costData.top_organizations && costData.top_organizations.length > 0 && (
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">Top AI Spenders</h2>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => router.push('/dashboard/admin/costs')}
                  >
                    View All <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
                
                <div className="space-y-3">
                  {costData.top_organizations.slice(0, 5).map((org, index) => (
                    <div key={org.org_name} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold text-sm">
                          {index + 1}
                        </div>
                        <span className="font-medium text-gray-900">{org.org_name}</span>
                      </div>
                      <span className="font-semibold text-gray-900">{formatCurrency(org.cost_usd)}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Quick Actions */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard/admin/organizations')}
              className="justify-start"
            >
              <Building2 className="w-5 h-5 mr-2" />
              View All Organizations
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard/admin/costs')}
              className="justify-start"
            >
              <BarChart3 className="w-5 h-5 mr-2" />
              Cost Analytics
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard/admin/health')}
              className="justify-start"
            >
              <Activity className="w-5 h-5 mr-2" />
              System Health
            </Button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}

