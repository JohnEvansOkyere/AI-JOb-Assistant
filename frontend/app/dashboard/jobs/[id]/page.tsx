/**
 * Job Detail Page
 * View and edit a specific job description
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { JobDescription } from '@/types'

export default function JobDetailPage() {
  const router = useRouter()
  const params = useParams()
  const jobId = params.id as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [job, setJob] = useState<JobDescription | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated && jobId) {
      loadJob()
    }
  }, [isAuthenticated, authLoading, jobId, router])

  const loadJob = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<JobDescription>(`/job-descriptions/${jobId}`)
      if (response.success && response.data) {
        setJob(response.data)
      } else {
        setError(response.message || 'Failed to load job')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
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

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <Button variant="outline" onClick={() => router.push('/dashboard/jobs')}>
              Back to Jobs
            </Button>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">{error || 'Job not found'}</p>
              <Button variant="outline" onClick={() => router.push('/dashboard/jobs')}>
                Back to Jobs
              </Button>
            </div>
          </Card>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
          <Button variant="outline" onClick={() => router.push('/dashboard/jobs')}>
            Back to Jobs
          </Button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Description</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{job.description}</p>
            </div>

            {job.requirements && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-2">Requirements</h2>
                <p className="text-gray-700 whitespace-pre-wrap">{job.requirements}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
              {job.location && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Location</p>
                  <p className="text-gray-900">{job.location}</p>
                </div>
              )}
              {job.employment_type && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Employment Type</p>
                  <p className="text-gray-900 capitalize">{job.employment_type}</p>
                </div>
              )}
              {job.experience_level && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Experience Level</p>
                  <p className="text-gray-900 capitalize">{job.experience_level}</p>
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-gray-500">Status</p>
                <span className={`inline-block px-2 py-1 rounded text-sm ${
                  job.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {job.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </Card>
      </main>
    </div>
  )
}

