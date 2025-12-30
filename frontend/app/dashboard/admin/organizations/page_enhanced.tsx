/**
 * Admin Organizations Page (Enhanced)
 * Comprehensive organization management with filtering, search, export, and admin controls
 */

'use client'

import { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { apiClient } from '@/lib/api/client'
import { 
  Building2, 
  Users, 
  FileText, 
  DollarSign, 
  Calendar, 
  ArrowUpDown, 
  Briefcase,
  Search,
  Download,
  Filter,
  X,
  MoreVertical,
  Pause,
  Play,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'

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
  subscription_plan?: string
  status?: string
  monthly_interview_limit?: number | null
  monthly_cost_limit_usd?: number | null
  daily_cost_limit_usd?: number | null
  billing_email?: string
  admin_notes?: string
}

export default function AdminOrganizationsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [sortBy, setSortBy] = useState<string>('last_activity')
  const [sortOrder, setSortOrder] = useState<string>('desc')
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [planFilter, setPlanFilter] = useState<string>('')
  const [showFilters, setShowFilters] = useState(false)

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
      loadOrganizations()
    }
  }, [isAuthenticated, authLoading, router, user, sortBy, sortOrder, statusFilter, planFilter])

  const loadOrganizations = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const params = new URLSearchParams({
        sort_by: sortBy,
        sort_order: sortOrder,
      })
      
      if (searchQuery) {
        params.append('search', searchQuery)
      }
      if (statusFilter) {
        params.append('status', statusFilter)
      }
      if (planFilter) {
        params.append('subscription_plan', planFilter)
      }

      const response = await apiClient.get<Organization[]>(
        `/admin/organizations?${params.toString()}`
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

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    // Debounce search - reload after user stops typing
    const timeoutId = setTimeout(() => {
      loadOrganizations()
    }, 500)
    return () => clearTimeout(timeoutId)
  }

  const exportToCSV = () => {
    const headers = [
      'Organization',
      'Status',
      'Plan',
      'Active Users',
      'Jobs Created',
      'Interviews Created',
      'Interviews Completed',
      'CVs Screened',
      'Monthly AI Cost (USD)',
      'Cost per Interview (USD)',
      'Last Activity'
    ]
    
    const rows = organizations.map(org => [
      org.org_name,
      org.status || 'active',
      org.subscription_plan || 'free',
      org.active_users.toString(),
      (org.jobs_created || 0).toString(),
      org.interviews_created.toString(),
      org.interviews_completed.toString(),
      org.cvs_screened.toString(),
      org.monthly_ai_cost_usd.toFixed(2),
      org.cost_per_interview_usd > 0 ? org.cost_per_interview_usd.toFixed(4) : '0.00',
      org.last_activity ? new Date(org.last_activity).toISOString() : ''
    ])
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `organizations_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const exportToJSON = () => {
    const dataStr = JSON.stringify(organizations, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `organizations_${new Date().toISOString().split('T')[0]}.json`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
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
        {status === 'trial' && <AlertTriangle className="w-3 h-3 mr-1" />}
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

  const clearFilters = () => {
    setSearchQuery('')
    setStatusFilter('')
    setPlanFilter('')
    setShowFilters(false)
  }

  const activeFilterCount = (searchQuery ? 1 : 0) + (statusFilter ? 1 : 0) + (planFilter ? 1 : 0)

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
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Organizations Overview</h1>
            <p className="text-gray-600 mt-1">Monitor customer usage and AI costs</p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              Filters
              {activeFilterCount > 0 && (
                <span className="bg-primary-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
                  {activeFilterCount}
                </span>
              )}
            </Button>
            <div className="relative">
              <Button
                variant="outline"
                onClick={() => {
                  const menu = document.getElementById('export-menu')
                  if (menu) {
                    menu.classList.toggle('hidden')
                  }
                }}
                className="flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export
              </Button>
              <div
                id="export-menu"
                className="hidden absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10"
              >
                <button
                  onClick={() => {
                    exportToCSV()
                    const menu = document.getElementById('export-menu')
                    if (menu) menu.classList.add('hidden')
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-t-lg"
                >
                  Export as CSV
                </button>
                <button
                  onClick={() => {
                    exportToJSON()
                    const menu = document.getElementById('export-menu')
                    if (menu) menu.classList.add('hidden')
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-b-lg"
                >
                  Export as JSON
                </button>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        {/* Filters */}
        {showFilters && (
          <Card>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
                {activeFilterCount > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={clearFilters}
                    className="flex items-center gap-2"
                  >
                    <X className="w-4 h-4" />
                    Clear All
                  </Button>
                )}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search Organizations
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value)
                        handleSearch(e.target.value)
                      }}
                      placeholder="Search by name..."
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status
                  </label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-900 text-sm"
                  >
                    <option value="">All Statuses</option>
                    <option value="active">Active</option>
                    <option value="paused">Paused</option>
                    <option value="suspended">Suspended</option>
                    <option value="trial">Trial</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subscription Plan
                  </label>
                  <select
                    value={planFilter}
                    onChange={(e) => setPlanFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-900 text-sm"
                  >
                    <option value="">All Plans</option>
                    <option value="free">Free</option>
                    <option value="starter">Starter</option>
                    <option value="professional">Professional</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Organizations Table */}
        <Card>
          {organizations.length === 0 ? (
            <div className="text-center py-12">
              <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-2">No organizations found.</p>
              {activeFilterCount > 0 && (
                <Button variant="outline" size="sm" onClick={clearFilters} className="mt-2">
                  Clear filters to see all organizations
                </Button>
              )}
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
                    <th className="py-3 pr-4">Status</th>
                    <th className="py-3 pr-4">Plan</th>
                    <th className="py-3 pr-4">
                      <button
                        onClick={() => handleSort('active_users')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Users
                        <ArrowUpDown className="w-3 h-3" />
                      </button>
                    </th>
                    <th className="py-3 pr-4">Jobs</th>
                    <th className="py-3 pr-4">Interviews</th>
                    <th className="py-3 pr-4">CVs</th>
                    <th className="py-3 pr-4">
                      <button
                        onClick={() => handleSort('monthly_ai_cost_usd')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Monthly Cost
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
                        {getStatusBadge(org.status)}
                      </td>
                      <td className="py-3 pr-4">
                        {getPlanBadge(org.subscription_plan)}
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
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => router.push(`/dashboard/admin/organizations/${encodeURIComponent(org.org_name)}`)}
                          >
                            View
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Summary Stats */}
          {organizations.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Total Organizations:</span>
                  <span className="ml-2 font-semibold text-gray-900">{organizations.length}</span>
                </div>
                <div>
                  <span className="text-gray-600">Total Users:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {organizations.reduce((sum, org) => sum + org.active_users, 0)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Total Monthly Cost:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {formatCurrency(organizations.reduce((sum, org) => sum + org.monthly_ai_cost_usd, 0))}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Total Interviews:</span>
                  <span className="ml-2 font-semibold text-gray-900">
                    {organizations.reduce((sum, org) => sum + org.interviews_completed, 0)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}

