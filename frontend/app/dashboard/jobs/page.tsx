/**
 * Jobs Page
 * List and manage job descriptions
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { ApiErrorHandler } from '@/lib/api/error-handler'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ErrorDisplay } from '@/components/ui/ErrorDisplay'
import { LoadingState } from '@/components/ui/LoadingState'
import { JobDescription } from '@/types'
import { Check, Copy } from 'lucide-react'

export default function JobsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [jobs, setJobs] = useState<JobDescription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copiedJobId, setCopiedJobId] = useState<string | null>(null)

  const handleCopyLink = async (jobId: string) => {
    const url = typeof window !== 'undefined' ? `${window.location.origin}/apply/${jobId}` : ''
    try {
      await navigator.clipboard.writeText(url)
      setCopiedJobId(jobId)
      setTimeout(() => setCopiedJobId(null), 2000)
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = url
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      setCopiedJobId(jobId)
      setTimeout(() => setCopiedJobId(null), 2000)
    }
  }

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
      const response = await apiClient.get<JobDescription[]>('/job-descriptions')
      if (response.success && response.data) {
        setJobs(response.data)
      } else {
        setError(response.message || 'Failed to load jobs')
      }
    } catch (err: any) {
      console.error('Error loading jobs:', err)
      // Use error handler for user-friendly messages
      const errorMessage = ApiErrorHandler.getErrorMessage(err)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadJobs()
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingState message="Loading jobs..." size="lg" />
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
            <h1 className="text-2xl font-bold text-gray-900">Job Descriptions</h1>
            <p className="text-gray-600 mt-1">Create and manage your job postings</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleRefresh} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
            <Button variant="primary" onClick={() => router.push('/dashboard/jobs/new')}>
              Create New Job
            </Button>
          </div>
        </div>

        {error && (
          <ErrorDisplay
            error={error}
            onRetry={loadJobs}
            onDismiss={() => setError('')}
            title="Failed to load jobs"
          />
        )}

        {jobs.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No job descriptions yet.</p>
              <Button variant="primary" onClick={() => router.push('/dashboard/jobs/new')}>
                Create Your First Job Description
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <Card key={job.id} title={job.title}>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 line-clamp-3">{job.description}</p>
                  {job.location && (
                    <p className="text-sm text-gray-500">📍 {job.location}</p>
                  )}
                  {job.experience_level && (
                    <p className="text-sm text-gray-500">Level: {job.experience_level}</p>
                  )}
                  <div className="space-y-2 pt-2">
                    <div className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-1 rounded ${
                        job.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {job.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleCopyLink(job.id)}
                        title="Copy application link"
                        className="flex items-center gap-1"
                      >
                        {copiedJobId === job.id ? (
                          <>
                            <Check className="w-3 h-3" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy Link</span>
                          </>
                        )}
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => router.push(`/dashboard/jobs/${job.id}/applications`)}
                      >
                        Applications
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => router.push(`/dashboard/jobs/${job.id}`)}
                      >
                        View
                      </Button>
                    </div>
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
