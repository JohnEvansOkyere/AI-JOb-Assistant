/**
 * CV Rankings Page
 * View all jobs with CV-screened candidates and access ranking views
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Briefcase, Users, CheckCircle, Clock, XCircle } from 'lucide-react'

interface JobWithRanking {
  id: string
  title: string
  description?: string
  is_active: boolean
  screened_count: number
  qualified_count: number
  maybe_qualified_count: number
  not_qualified_count: number
}

export default function RankingsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [jobs, setJobs] = useState<JobWithRanking[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadJobs()
    }
  }, [isAuthenticated, authLoading, router])

  const loadJobs = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.get<JobWithRanking[]>('/rankings/cv/jobs')
      
      if (response.success && response.data) {
        setJobs(response.data)
      } else {
        setError(response.message || 'Failed to load jobs')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading rankings...</p>
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
            <h1 className="text-2xl font-bold text-gray-900">CV Rankings</h1>
            <p className="text-gray-600 mt-1">View ranked candidates by job based on CV screening scores</p>
          </div>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        {jobs.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No jobs with screened candidates found.</p>
              <Button variant="outline" onClick={() => router.push('/dashboard/jobs')}>
                View Job Descriptions
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {jobs.map((job) => (
              <Card key={job.id}>
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Briefcase className="w-5 h-5 text-gray-500" />
                        <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                      </div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          job.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {job.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-700">Total Screened</span>
                      </div>
                      <span className="font-semibold text-gray-900">{job.screened_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-gray-700">Qualified</span>
                      </div>
                      <span className="font-semibold text-green-600">{job.qualified_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-yellow-600" />
                        <span className="text-gray-700">Maybe Qualified</span>
                      </div>
                      <span className="font-semibold text-yellow-600">{job.maybe_qualified_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <XCircle className="w-4 h-4 text-red-600" />
                        <span className="text-gray-700">Not Qualified</span>
                      </div>
                      <span className="font-semibold text-red-600">{job.not_qualified_count}</span>
                    </div>
                  </div>

                  {job.screened_count > 0 && (
                    <Button
                      variant="primary"
                      className="w-full"
                      onClick={() => router.push(`/dashboard/rankings/cv/job/${job.id}`)}
                    >
                      View Ranked List
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

