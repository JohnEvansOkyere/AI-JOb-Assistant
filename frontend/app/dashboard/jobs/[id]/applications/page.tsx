/**
 * Job Applications Page
 * View and screen applications for a specific job
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

interface Application {
  id: string
  candidate_id: string
  cv_id: string
  status: string
  applied_at: string
  screened_at?: string
  candidates?: { full_name: string; email: string }
  cv_screening_results?: {
    match_score: number
    recommendation: string
    strengths: string[]
    gaps: string[]
  }
}

export default function JobApplicationsPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [screening, setScreening] = useState(false)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<string>('all') // all, pending, qualified, rejected

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadApplications()
    }
  }, [isAuthenticated, authLoading, router, filter])

  const loadApplications = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const statusParam = filter !== 'all' ? `?status=${filter}` : ''
      const response = await apiClient.get<Application[]>(`/applications/job/${jobId}${statusParam}`)
      
      if (response.success && response.data) {
        setApplications(response.data)
      } else {
        setError(response.message || 'Failed to load applications')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleScreenAll = async () => {
    try {
      setScreening(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.post(`/applications/job/${jobId}/screen-all`)
      
      if (response.success) {
        alert(`Screened ${response.data?.screened || 0} applications. ${response.data?.qualified || 0} qualified.`)
        loadApplications() // Reload to show results
      } else {
        setError(response.message || 'Screening failed')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setScreening(false)
    }
  }

  const handleScreenOne = async (applicationId: string) => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.post(`/applications/${applicationId}/screen`)
      
      if (response.success) {
        alert('Application screened successfully')
        loadApplications()
      } else {
        setError(response.message || 'Screening failed')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    }
  }

  const getRecommendationColor = (recommendation?: string) => {
    if (!recommendation) return 'bg-gray-100 text-gray-800'
    if (recommendation === 'qualified') return 'bg-green-100 text-green-800'
    if (recommendation === 'maybe_qualified') return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
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
            <h1 className="text-2xl font-bold text-gray-900">Job Applications</h1>
            <p className="text-gray-600 mt-1">Review and screen candidate applications</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push(`/dashboard/jobs/${jobId}`)}>
              Back to Job
            </Button>
            <Button 
              variant="primary" 
              onClick={handleScreenAll}
              loading={screening}
              disabled={screening}
            >
              Screen All Pending
            </Button>
          </div>
        </div>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Filter */}
        <div className="mb-6">
          <div className="flex gap-2">
            {['all', 'pending', 'qualified', 'rejected'].map((status) => (
              <Button
                key={status}
                variant={filter === status ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setFilter(status)}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </Button>
            ))}
          </div>
        </div>

        {/* Applications List */}
        {applications.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No applications found.</p>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {applications.map((app) => (
              <Card key={app.id}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {app.candidates?.full_name || 'Unknown'}
                      </h3>
                      <span className={`text-xs px-2 py-1 rounded ${getRecommendationColor(app.cv_screening_results?.recommendation)}`}>
                        {app.cv_screening_results?.recommendation?.replace('_', ' ') || app.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{app.candidates?.email}</p>
                    <p className="text-xs text-gray-500">
                      Applied: {new Date(app.applied_at).toLocaleDateString()}
                    </p>
                    
                    {app.cv_screening_results && (
                      <div className="mt-4 p-3 bg-gray-50 rounded">
                        <div className="flex items-center gap-4 mb-2">
                          <span className="text-sm font-medium">Match Score: {app.cv_screening_results.match_score}%</span>
                        </div>
                        {app.cv_screening_results.strengths && app.cv_screening_results.strengths.length > 0 && (
                          <div className="mb-2">
                            <p className="text-xs font-medium text-green-700 mb-1">Strengths:</p>
                            <ul className="text-xs text-gray-600 list-disc list-inside">
                              {app.cv_screening_results.strengths.slice(0, 3).map((s, i) => (
                                <li key={i}>{s}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {app.cv_screening_results.gaps && app.cv_screening_results.gaps.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-red-700 mb-1">Gaps:</p>
                            <ul className="text-xs text-gray-600 list-disc list-inside">
                              {app.cv_screening_results.gaps.slice(0, 3).map((g, i) => (
                                <li key={i}>{g}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-2 ml-4">
                    {app.status === 'pending' && !app.cv_screening_results && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleScreenOne(app.id)}
                      >
                        Screen
                      </Button>
                    )}
                    {app.cv_screening_results?.recommendation === 'qualified' && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => router.push(`/dashboard/jobs/${jobId}/applications/${app.id}/create-ticket`)}
                      >
                        Create Interview Ticket
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/jobs/${jobId}/applications/${app.id}`)}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

