/**
 * Admin Subscriptions Page
 * Comprehensive subscription monitoring and management
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { apiClient } from '@/lib/api/client'
import { 
  CreditCard, 
  Users, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle,
  Search,
  Filter,
  RefreshCw,
  DollarSign,
  Calendar,
  BarChart3
} from 'lucide-react'
import { LineChart, BarChart } from '@/components/ui/SimpleChart'

interface Subscription {
  company_name: string
  subscription_plan: string
  status: 'active' | 'trial' | 'paused' | 'suspended'
  trial_ends_at?: string
  subscription_starts_at?: string
  subscription_ends_at?: string
  last_payment_date?: string
  next_payment_date?: string
  monthly_revenue_usd: number
  monthly_interview_limit?: number
  monthly_cost_limit_usd?: number
  daily_cost_limit_usd?: number
  current_monthly_interviews: number
  current_monthly_cost_usd: number
  current_daily_cost_usd: number
  billing_email?: string
}

interface SubscriptionStats {
  total_subscriptions: number
  active_subscriptions: number
  trial_subscriptions: number
  paused_subscriptions: number
  suspended_subscriptions: number
  monthly_recurring_revenue_usd: number
  estimated_total_revenue_usd: number
  plan_distribution: Record<string, number>
  trial_conversion_rate: number
}

export default function AdminSubscriptionsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [stats, setStats] = useState<SubscriptionStats | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [planFilter, setPlanFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    if (authLoading) return
    
    if (!user) {
      router.push('/auth/login')
      return
    }

    // Check admin status (you may need to adjust this based on your auth system)
    loadSubscriptions()
    loadStats()
  }, [user, authLoading, router])

  const loadSubscriptions = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (planFilter !== 'all') params.append('subscription_plan', planFilter)
      if (statusFilter !== 'all') params.append('status', statusFilter)

      const response = await apiClient.get<{
        subscriptions: Subscription[]
        total: number
        limit: number
        offset: number
      }>(`/admin/subscriptions?${params.toString()}`)

      if (response.success && response.data) {
        setSubscriptions(response.data.subscriptions || [])
      }
    } catch (err: any) {
      if (err.message?.includes('403') || err.message?.includes('Admin access required')) {
        setError('Admin access required. You do not have permission to view this page.')
        router.push('/dashboard')
      } else {
        setError(err.message || 'Failed to load subscriptions')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.get<SubscriptionStats>('/admin/subscriptions/stats')

      if (response.success && response.data) {
        setStats(response.data)
      }
    } catch (err: any) {
      console.error('Failed to load subscription stats', err)
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

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      trial: 'bg-blue-100 text-blue-800',
      paused: 'bg-yellow-100 text-yellow-800',
      suspended: 'bg-red-100 text-red-800',
    }
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const getPlanBadge = (plan: string) => {
    const colors = {
      free: 'bg-gray-100 text-gray-800',
      starter: 'bg-blue-100 text-blue-800',
      professional: 'bg-purple-100 text-purple-800',
      enterprise: 'bg-gold-100 text-gold-800',
      custom: 'bg-indigo-100 text-indigo-800',
    }
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[plan as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
        {plan.charAt(0).toUpperCase() + plan.slice(1)}
      </span>
    )
  }

  const filteredSubscriptions = subscriptions.filter(sub => {
    if (searchQuery && !sub.company_name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    return true
  })

  if (loading && !stats) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-turquoise mb-4" />
            <p className="text-gray-600">Loading subscriptions...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <Card className="p-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <p>{error}</p>
          </div>
        </Card>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Subscription Management</h1>
            <p className="text-gray-600 mt-1">Monitor and manage all subscriptions</p>
          </div>
          <Button onClick={() => { loadSubscriptions(); loadStats(); }} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Summary Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Subscriptions"
              value={stats.total_subscriptions.toString()}
              icon={<CreditCard className="w-6 h-6" />}
            />
            <StatCard
              title="Active Subscriptions"
              value={stats.active_subscriptions.toString()}
              icon={<CheckCircle className="w-6 h-6" />}
            />
            <StatCard
              title="Monthly Recurring Revenue"
              value={formatCurrency(stats.monthly_recurring_revenue_usd)}
              icon={<DollarSign className="w-6 h-6" />}
            />
            <StatCard
              title="Trial Conversion Rate"
              value={`${stats.trial_conversion_rate.toFixed(1)}%`}
              icon={<TrendingUp className="w-6 h-6" />}
            />
          </div>
        )}

        {/* Filters */}
        <Card className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by company name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <select
              value={planFilter}
              onChange={(e) => setPlanFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-turquoise"
            >
              <option value="all">All Plans</option>
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
              <option value="custom">Custom</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-turquoise"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="trial">Trial</option>
              <option value="paused">Paused</option>
              <option value="suspended">Suspended</option>
            </select>
            <Button onClick={loadSubscriptions} variant="primary">
              <Filter className="h-4 w-4 mr-2" />
              Apply
            </Button>
          </div>
        </Card>

        {/* Subscriptions Table */}
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Organization</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monthly Revenue</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Next Payment</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSubscriptions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                      No subscriptions found
                    </td>
                  </tr>
                ) : (
                  filteredSubscriptions.map((subscription) => (
                    <tr key={subscription.company_name} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900">{subscription.company_name}</div>
                        {subscription.billing_email && (
                          <div className="text-sm text-gray-500">{subscription.billing_email}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getPlanBadge(subscription.subscription_plan)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(subscription.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatCurrency(subscription.monthly_revenue_usd)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm">
                          <div>Interviews: {subscription.current_monthly_interviews} / {subscription.monthly_interview_limit || '∞'}</div>
                          <div className="text-gray-500">Cost: {formatCurrency(subscription.current_monthly_cost_usd)}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(subscription.next_payment_date || subscription.trial_ends_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <Button
                          variant="ghost"
                          onClick={() => router.push(`/dashboard/admin/organizations/${encodeURIComponent(subscription.company_name)}`)}
                        >
                          View Details
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Plan Distribution Chart */}
        {stats && stats.plan_distribution && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Plan Distribution</h2>
            <BarChart
              data={Object.entries(stats.plan_distribution).map(([plan, count]) => ({
                label: plan.charAt(0).toUpperCase() + plan.slice(1),
                value: count,
                color: "#20B2AA"
              }))}
            />
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}

