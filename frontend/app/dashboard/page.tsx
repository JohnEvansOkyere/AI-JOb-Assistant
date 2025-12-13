/**
 * Dashboard Page
 * Modern recruiter dashboard with statistics and quick actions
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { StatCard } from '@/components/ui/StatCard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/lib/api/client'

interface DashboardStats {
  total_jobs: number
  active_jobs: number
  total_applications: number
  pending_applications: number
  qualified_candidates: number
  total_interviews: number
  completed_interviews: number
}

export default function DashboardPage() {
  const router = useRouter()
  const { loading: authLoading, isAuthenticated } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated && mounted) {
      loadStats()
    }
  }, [isAuthenticated, authLoading, router, mounted])

  const loadStats = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.get<DashboardStats>('/stats/dashboard')
      
      if (response.success && response.data) {
        setStats(response.data)
      } else {
        setError(response.message || 'Failed to load statistics')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (!mounted || authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading dashboard...</p>
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
        {/* Welcome Section */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome back!</h1>
          <p className="text-gray-600 mt-2">Here's what's happening with your recruitment pipeline.</p>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Jobs"
            value={stats?.total_jobs || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
            onClick={() => router.push('/dashboard/jobs')}
          />
          
          <StatCard
            title="Active Jobs"
            value={stats?.active_jobs || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            onClick={() => router.push('/dashboard/jobs')}
          />
          
          <StatCard
            title="Applications"
            value={stats?.total_applications || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
            trend={
              stats?.pending_applications
                ? {
                    value: Math.round((stats.pending_applications / (stats.total_applications || 1)) * 100),
                    label: 'pending',
                    positive: false,
                  }
                : undefined
            }
            onClick={() => router.push('/dashboard/applications')}
          />
          
          <StatCard
            title="Qualified Candidates"
            value={stats?.qualified_candidates || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            onClick={() => router.push('/dashboard/candidates')}
          />
        </div>

        {/* Quick Actions & Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quick Actions */}
          <Card title="Quick Actions">
            <div className="space-y-3">
              <Button
                variant="primary"
                onClick={() => router.push('/dashboard/jobs/new')}
                className="w-full justify-start"
                size="lg"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create New Job Description
              </Button>
              
              <Button
                variant="outline"
                onClick={() => router.push('/dashboard/jobs')}
                className="w-full justify-start"
                size="lg"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Manage Job Descriptions
              </Button>
              
              <Button
                variant="outline"
                onClick={() => router.push('/dashboard/applications')}
                className="w-full justify-start"
                size="lg"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Review Applications
              </Button>
            </div>
          </Card>

          {/* Pipeline Overview */}
          <Card title="Pipeline Overview">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Pending Applications</span>
                <span className="text-lg font-semibold text-gray-900">{stats?.pending_applications || 0}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-yellow-500 h-2 rounded-full transition-all"
                  style={{
                    width: stats?.total_applications
                      ? `${((stats.pending_applications || 0) / stats.total_applications) * 100}%`
                      : '0%',
                  }}
                />
              </div>
              
              <div className="flex items-center justify-between pt-2">
                <span className="text-sm text-gray-600">Qualified Candidates</span>
                <span className="text-lg font-semibold text-green-600">{stats?.qualified_candidates || 0}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{
                    width: stats?.total_applications
                      ? `${((stats.qualified_candidates || 0) / stats.total_applications) * 100}%`
                      : '0%',
                  }}
                />
              </div>
              
              <div className="flex items-center justify-between pt-2">
                <span className="text-sm text-gray-600">Completed Interviews</span>
                <span className="text-lg font-semibold text-primary-600">{stats?.completed_interviews || 0}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-500 h-2 rounded-full transition-all"
                  style={{
                    width: stats?.total_interviews
                      ? `${((stats.completed_interviews || 0) / stats.total_interviews) * 100}%`
                      : '0%',
                  }}
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Additional Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StatCard
            title="Total Interviews"
            value={stats?.total_interviews || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            }
            onClick={() => router.push('/dashboard/interviews')}
          />
        </div>
      </div>
    </DashboardLayout>
  )
}
