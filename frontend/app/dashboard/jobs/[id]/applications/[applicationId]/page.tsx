/**
 * Application Details Page
 * View detailed information about a specific job application
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

interface CV {
  id: string
  file_name: string
  file_path: string
  file_size?: number
  mime_type?: string
  parsed_text?: string
}

interface Application {
  id: string
  candidate_id: string
  job_description_id: string
  cv_id: string
  status: string
  cover_letter?: string
  applied_at: string
  screened_at?: string
  candidates?: {
    id: string
    full_name: string
    email: string
    phone?: string
  }
  job_descriptions?: {
    id: string
    title: string
    description?: string
  }
  cv_screening_results?: {
    match_score: number
    skill_match_score?: number
    experience_match_score?: number
    qualification_match_score?: number
    strengths?: string[]
    gaps?: string[]
    recommendation: string
    screening_notes?: string
    screened_at?: string
  }
  cvs?: CV
}

export default function ApplicationDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string
  const applicationId = params.applicationId as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [application, setApplication] = useState<Application | null>(null)
  const [loading, setLoading] = useState(true)
  const [screening, setScreening] = useState(false)
  const [error, setError] = useState('')
  const [cvDownloadUrl, setCvDownloadUrl] = useState<string | null>(null)
  const [loadingCv, setLoadingCv] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadApplication()
    }
  }, [isAuthenticated, authLoading, router, applicationId])

  const loadApplication = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      // Get application from the list endpoint (it includes related data)
      const response = await apiClient.get<Application[]>(`/applications/job/${jobId}`)
      
      if (response.success && response.data) {
        const app = response.data.find(a => a.id === applicationId)
        if (app) {
          // Handle CV data that might come as array from Supabase nested select
          if (app.cvs && Array.isArray(app.cvs) && app.cvs.length > 0) {
            app.cvs = app.cvs[0]
          }
          setApplication(app)
          // Load CV download URL if CV exists
          if (app.cv_id) {
            loadCvDownloadUrl(app.cv_id)
          }
        } else {
          setError('Application not found')
        }
      } else {
        setError(response.message || 'Failed to load application')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const loadCvDownloadUrl = async (cvId: string) => {
    try {
      setLoadingCv(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.get<{ download_url: string; file_name: string; mime_type: string }>(`/cvs/${cvId}/download-url`)
      
      if (response.success && response.data) {
        setCvDownloadUrl(response.data.download_url)
      }
    } catch (err: any) {
      console.error('Error loading CV download URL:', err)
      // Don't show error to user, just log it
    } finally {
      setLoadingCv(false)
    }
  }

  const handleScreen = async () => {
    try {
      setScreening(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.post(`/applications/${applicationId}/screen`)
      
      if (response.success) {
        // Reload application to show updated screening results
        await loadApplication()
      } else {
        setError(response.message || 'Screening failed')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setScreening(false)
    }
  }

  const getRecommendationColor = (recommendation?: string) => {
    if (!recommendation) return 'bg-gray-100 text-gray-800'
    if (recommendation === 'qualified') return 'bg-green-100 text-green-800'
    if (recommendation === 'maybe_qualified') return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const getStatusColor = (status: string) => {
    if (status === 'qualified') return 'bg-green-100 text-green-800'
    if (status === 'rejected') return 'bg-red-100 text-red-800'
    if (status === 'pending') return 'bg-yellow-100 text-yellow-800'
    return 'bg-gray-100 text-gray-800'
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading application details...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  if (!application) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Application Details</h1>
            </div>
            <Button variant="outline" onClick={() => router.push(`/dashboard/jobs/${jobId}/applications`)}>
              Back to Applications
            </Button>
          </div>
          {error && (
            <Card>
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            </Card>
          )}
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Application Details</h1>
            <p className="text-gray-600 mt-1">
              Application for {application.job_descriptions?.title || 'Job'}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push(`/dashboard/jobs/${jobId}/applications`)}>
              Back to Applications
            </Button>
            {application.status === 'pending' && !application.cv_screening_results && (
              <Button 
                variant="primary" 
                onClick={handleScreen}
                disabled={screening}
                loading={screening}
              >
                {screening ? 'Screening...' : 'Screen Application'}
              </Button>
            )}
            {application.cv_screening_results?.recommendation === 'qualified' && (
              <Button
                variant="primary"
                onClick={() => router.push(`/dashboard/jobs/${jobId}/applications/${applicationId}/create-ticket`)}
              >
                Issue Interview Ticket
              </Button>
            )}
          </div>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        {/* Candidate Information */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Candidate Information</h2>
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-700">Full Name</label>
              <p className="text-gray-900">{application.candidates?.full_name || 'N/A'}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Email</label>
              <p className="text-gray-900">{application.candidates?.email || 'N/A'}</p>
            </div>
            {application.candidates?.phone && (
              <div>
                <label className="text-sm font-medium text-gray-700">Phone</label>
                <p className="text-gray-900">{application.candidates.phone}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Application Details */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Details</h2>
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-700">Status</label>
              <div className="mt-1">
                <span className={`text-xs px-2 py-1 rounded ${getStatusColor(application.status)}`}>
                  {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                </span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Applied At</label>
              <p className="text-gray-900">
                {new Date(application.applied_at).toLocaleString()}
              </p>
            </div>
            {application.screened_at && (
              <div>
                <label className="text-sm font-medium text-gray-700">Screened At</label>
                <p className="text-gray-900">
                  {new Date(application.screened_at).toLocaleString()}
                </p>
              </div>
            )}
            {application.cover_letter && (
              <div>
                <label className="text-sm font-medium text-gray-700">Cover Letter</label>
                <div className="mt-1 p-3 bg-gray-50 rounded text-gray-900 whitespace-pre-wrap">
                  {application.cover_letter}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* CV Document */}
        {application.cv_id && (
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">CV / Resume</h2>
            <div className="space-y-3">
              {application.cvs && (
                <div>
                  <label className="text-sm font-medium text-gray-700">File Name</label>
                  <p className="text-gray-900">{application.cvs.file_name || 'CV Document'}</p>
                  {application.cvs.file_size && (
                    <p className="text-sm text-gray-600 mt-1">
                      {(application.cvs.file_size / 1024).toFixed(2)} KB
                    </p>
                  )}
                </div>
              )}
              <div className="flex gap-2">
                {cvDownloadUrl ? (
                  <>
                    <Button
                      variant="primary"
                      onClick={() => window.open(cvDownloadUrl, '_blank')}
                    >
                      View CV
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        const link = document.createElement('a')
                        link.href = cvDownloadUrl
                        link.download = application.cvs?.file_name || 'cv.pdf'
                        link.click()
                      }}
                    >
                      Download CV
                    </Button>
                  </>
                ) : loadingCv ? (
                  <Button variant="outline" disabled>
                    Loading CV...
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    onClick={() => loadCvDownloadUrl(application.cv_id)}
                  >
                    Load CV
                  </Button>
                )}
              </div>
              {application.cvs?.parsed_text && (
                <div className="mt-4">
                  <label className="text-sm font-medium text-gray-700 mb-2 block">CV Text Content</label>
                  <div className="p-3 bg-gray-50 rounded text-gray-900 whitespace-pre-wrap max-h-96 overflow-y-auto text-sm">
                    {application.cvs.parsed_text}
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Screening Results */}
        {application.cv_screening_results && (
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">CV Screening Results</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Overall Match Score</label>
                  <p className="text-2xl font-bold text-gray-900">
                    {application.cv_screening_results.match_score}%
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Recommendation</label>
                  <div className="mt-1">
                    <span className={`text-xs px-2 py-1 rounded ${getRecommendationColor(application.cv_screening_results.recommendation)}`}>
                      {application.cv_screening_results.recommendation.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              {(application.cv_screening_results.skill_match_score || 
                application.cv_screening_results.experience_match_score || 
                application.cv_screening_results.qualification_match_score) && (
                <div className="grid grid-cols-3 gap-4">
                  {application.cv_screening_results.skill_match_score && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Skill Match</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {application.cv_screening_results.skill_match_score}%
                      </p>
                    </div>
                  )}
                  {application.cv_screening_results.experience_match_score && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Experience Match</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {application.cv_screening_results.experience_match_score}%
                      </p>
                    </div>
                  )}
                  {application.cv_screening_results.qualification_match_score && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Qualification Match</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {application.cv_screening_results.qualification_match_score}%
                      </p>
                    </div>
                  )}
                </div>
              )}

              {application.cv_screening_results.strengths && application.cv_screening_results.strengths.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-green-700 mb-2 block">Strengths</label>
                  <ul className="list-disc list-inside space-y-1">
                    {application.cv_screening_results.strengths.map((strength, index) => (
                      <li key={index} className="text-gray-700">{strength}</li>
                    ))}
                  </ul>
                </div>
              )}

              {application.cv_screening_results.gaps && application.cv_screening_results.gaps.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-red-700 mb-2 block">Gaps / Areas for Improvement</label>
                  <ul className="list-disc list-inside space-y-1">
                    {application.cv_screening_results.gaps.map((gap, index) => (
                      <li key={index} className="text-gray-700">{gap}</li>
                    ))}
                  </ul>
                </div>
              )}

              {application.cv_screening_results.screening_notes && (
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">AI Screening Analysis</label>
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded text-gray-900 whitespace-pre-wrap">
                    {application.cv_screening_results.screening_notes}
                  </div>
                </div>
              )}

              {/* Action Button for Qualified Candidates */}
              {application.cv_screening_results.recommendation === 'qualified' && (
                <div className="pt-4 border-t">
                  <Button
                    variant="primary"
                    onClick={() => router.push(`/dashboard/jobs/${jobId}/applications/${applicationId}/create-ticket`)}
                    className="w-full"
                  >
                    Issue Interview Ticket
                  </Button>
                </div>
              )}
            </div>
          </Card>
        )}

        {!application.cv_screening_results && application.status === 'pending' && (
          <Card>
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">This application has not been screened yet.</p>
              <Button variant="primary" onClick={handleScreen} disabled={screening} loading={screening}>
                {screening ? 'Screening...' : 'Screen Application'}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}

