/**
 * Applications Overview Page
 * View all applications across all jobs
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/lib/api/client'
import { Briefcase, User, Mail, Calendar, CheckCircle, Clock, XCircle, Filter, ChevronDown } from 'lucide-react'
import { JobDescription } from '@/types'

interface Application {
  id: string
  job_description_id: string
  candidate_id: string
  status: string
  applied_at: string
  cover_letter?: string
  candidates?: {
    full_name: string
    email: string
    phone?: string
  }
  job_descriptions?: {
    id: string
    title: string
  }
  cv_screening_results?: {
    match_score: number
    recommendation: string
    strengths?: string[]
    gaps?: string[]
  }
}

export default function ApplicationsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [applications, setApplications] = useState<Application[]>([])
  const [jobs, setJobs] = useState<JobDescription[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingJobs, setLoadingJobs] = useState(true)
  const [error, setError] = useState('')
  const [selectedJobId, setSelectedJobId] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadApplications()
      loadJobs()
    }
  }, [isAuthenticated, authLoading, router])

  const loadApplications = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<Application[]>('/applications')
      if (response.success && response.data) {
        setApplications(response.data)
      } else {
        setError(response.message || 'Failed to load applications')
      }
    } catch (err: any) {
      console.error('Error loading applications:', err)
      setError(err.message || 'An error occurred while loading applications')
    } finally {
      setLoading(false)
    }
  }

  const loadJobs = async () => {
    try {
      setLoadingJobs(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<JobDescription[]>('/job-descriptions')
      if (response.success && response.data) {
        setJobs(response.data)
      }
    } catch (err: any) {
      console.error('Error loading jobs:', err)
    } finally {
      setLoadingJobs(false)
    }
  }

  const filteredApplications = applications.filter(app => {
    const matchesJob = selectedJobId === 'all' || app.job_description_id === selectedJobId
    const matchesStatus = statusFilter === 'all' || app.status === statusFilter
    
    return matchesJob && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800', icon: Clock },
      qualified: { label: 'Qualified', className: 'bg-green-100 text-green-800', icon: CheckCircle },
      screening: { label: 'Screening', className: 'bg-blue-100 text-blue-800', icon: Clock },
      rejected: { label: 'Rejected', className: 'bg-red-100 text-red-800', icon: XCircle },
      interview_scheduled: { label: 'Interview Scheduled', className: 'bg-purple-100 text-purple-800', icon: Calendar },
    }
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
    const Icon = config.icon
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${config.className}`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </span>
    )
  }

  // Calculate status counts based on job-filtered applications
  const jobFilteredApplications = selectedJobId === 'all' 
    ? applications 
    : applications.filter(app => app.job_description_id === selectedJobId)
  
  const statusCounts = {
    all: jobFilteredApplications.length,
    pending: jobFilteredApplications.filter(a => a.status === 'pending').length,
    qualified: jobFilteredApplications.filter(a => a.status === 'qualified').length,
    screening: jobFilteredApplications.filter(a => a.status === 'screening').length,
    rejected: jobFilteredApplications.filter(a => a.status === 'rejected').length,
    interview_scheduled: jobFilteredApplications.filter(a => a.status === 'interview_scheduled').length,
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading applications...</p>
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
            <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
            <p className="text-gray-600 mt-1">View and manage all job applications</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadApplications} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
            <Button variant="primary" onClick={() => router.push('/dashboard/jobs')}>
              View Jobs
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md dark:shadow-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-gray-400 dark:text-gray-500" />
              <div className="relative flex-1">
                <select
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white appearance-none cursor-pointer"
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  disabled={loadingJobs}
                >
                  <option value="all">All Job Posts ({applications.length})</option>
                  {jobs.map((job) => {
                    const jobApplicationCount = applications.filter(
                      app => app.job_description_id === job.id
                    ).length
                    return (
                      <option key={job.id} value={job.id}>
                        {job.title} ({jobApplicationCount})
                      </option>
                    )
                  })}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-gray-500 pointer-events-none" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5 text-gray-400 dark:text-gray-500" />
              <div className="relative flex-1">
                <select
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white appearance-none cursor-pointer"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Status ({statusCounts.all})</option>
                  <option value="pending">Pending ({statusCounts.pending})</option>
                  <option value="screening">Screening ({statusCounts.screening})</option>
                  <option value="qualified">Qualified ({statusCounts.qualified})</option>
                  <option value="rejected">Rejected ({statusCounts.rejected})</option>
                  <option value="interview_scheduled">Interview Scheduled ({statusCounts.interview_scheduled})</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-gray-500 pointer-events-none" />
              </div>
            </div>
          </div>
        </div>

        {filteredApplications.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <Briefcase className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {selectedJobId !== 'all' || statusFilter !== 'all'
                  ? 'No applications match your filters.'
                  : 'No applications yet.'}
              </p>
              {selectedJobId === 'all' && statusFilter === 'all' && (
                <Button variant="primary" onClick={() => router.push('/dashboard/jobs')}>
                  View Job Postings
                </Button>
              )}
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredApplications.map((app) => (
              <Card key={app.id}>
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                          <User className="h-5 w-5 text-gray-400" />
                          {app.candidates?.full_name || 'Unknown Candidate'}
                        </h3>
                        <div className="mt-1 space-y-1">
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Mail className="h-4 w-4" />
                            {app.candidates?.email}
                          </div>
                          {app.candidates?.phone && (
                            <div className="text-sm text-gray-600">
                              {app.candidates.phone}
                            </div>
                          )}
                        </div>
                      </div>
                      {getStatusBadge(app.status)}
                    </div>

                    <div className="border-t pt-3 space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Briefcase className="h-4 w-4 text-gray-400" />
                        <span className="font-medium text-gray-900">
                          {app.job_descriptions?.title || 'Unknown Job'}
                        </span>
                      </div>

                      {app.cv_screening_results && (
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-600">Match Score:</span>
                            <span className={`font-semibold ${
                              app.cv_screening_results.match_score >= 70
                                ? 'text-green-600'
                                : app.cv_screening_results.match_score >= 50
                                ? 'text-yellow-600'
                                : 'text-red-600'
                            }`}>
                              {app.cv_screening_results.match_score}%
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-gray-600">Recommendation:</span>
                            <span className="font-medium capitalize">
                              {app.cv_screening_results.recommendation?.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                      )}

                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Calendar className="h-3 w-3" />
                        Applied {new Date(app.applied_at).toLocaleDateString()} at {new Date(app.applied_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/jobs/${app.job_description_id}/applications/${app.id}`)}
                    >
                      View Details
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/jobs/${app.job_description_id}/applications`)}
                    >
                      View Job
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
