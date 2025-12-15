/**
 * Candidate Details Page
 * View detailed information about a specific candidate and all their applications
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { User, Mail, Phone, Briefcase, Calendar, CheckCircle, Clock, XCircle } from 'lucide-react'

interface Application {
  id: string
  job_description_id: string
  status: string
  applied_at: string
  screened_at?: string
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
}

interface Candidate {
  id: string
  full_name: string
  email: string
  phone?: string
  created_at: string
  applications: Application[]
}

export default function CandidateDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const candidateId = params.candidateId as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [candidate, setCandidate] = useState<Candidate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadCandidate()
    }
  }, [isAuthenticated, authLoading, router, candidateId])

  const loadCandidate = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.get<Candidate>(`/candidates/${candidateId}`)
      
      if (response.success && response.data) {
        setCandidate(response.data)
      } else {
        setError(response.message || 'Failed to load candidate')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
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
            <p className="mt-4 text-gray-600">Loading candidate details...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  if (!candidate) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Candidate Details</h1>
            </div>
            <Button variant="outline" onClick={() => router.push('/dashboard/candidates')}>
              Back to Candidates
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
            <h1 className="text-2xl font-bold text-gray-900">Candidate Details</h1>
            <p className="text-gray-600 mt-1">{candidate.full_name}</p>
          </div>
          <Button variant="outline" onClick={() => router.push('/dashboard/candidates')}>
            Back to Candidates
          </Button>
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
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <User className="w-5 h-5 text-gray-500" />
              <div>
                <label className="text-sm font-medium text-gray-700">Full Name</label>
                <p className="text-gray-900">{candidate.full_name}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-gray-500" />
              <div>
                <label className="text-sm font-medium text-gray-700">Email</label>
                <p className="text-gray-900">{candidate.email}</p>
              </div>
            </div>
            {candidate.phone && (
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-gray-500" />
                <div>
                  <label className="text-sm font-medium text-gray-700">Phone</label>
                  <p className="text-gray-900">{candidate.phone}</p>
                </div>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-gray-500" />
              <div>
                <label className="text-sm font-medium text-gray-700">Member Since</label>
                <p className="text-gray-900">
                  {new Date(candidate.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Applications */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Applications ({candidate.applications.length})
          </h2>
          {candidate.applications.length === 0 ? (
            <p className="text-gray-600">No applications found.</p>
          ) : (
            <div className="space-y-4">
              {candidate.applications.map((app) => (
                <div key={app.id} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Briefcase className="w-5 h-5 text-gray-500" />
                        <h3 className="text-lg font-semibold text-gray-900">
                          {app.job_descriptions?.title || 'Unknown Job'}
                        </h3>
                      </div>
                      <div className="flex items-center gap-4 mb-2">
                        <span className={`text-xs px-2 py-1 rounded ${getStatusColor(app.status)}`}>
                          {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                        </span>
                        {app.cv_screening_results && (
                          <span className={`text-xs px-2 py-1 rounded ${getRecommendationColor(app.cv_screening_results.recommendation)}`}>
                            {app.cv_screening_results.recommendation.replace('_', ' ').toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        <span>Applied: {new Date(app.applied_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/jobs/${app.job_description_id}/applications/${app.id}`)}
                    >
                      View Application
                    </Button>
                  </div>

                  {/* Screening Results */}
                  {app.cv_screening_results && (
                    <div className="mt-4 p-3 bg-gray-50 rounded space-y-2">
                      <div className="flex items-center gap-4">
                        <div>
                          <label className="text-sm font-medium text-gray-700">Match Score</label>
                          <p className="text-lg font-bold text-green-600">
                            {app.cv_screening_results.match_score}%
                          </p>
                        </div>
                        {app.cv_screening_results.skill_match_score && (
                          <div>
                            <label className="text-sm font-medium text-gray-700">Skill Match</label>
                            <p className="text-sm font-semibold text-gray-900">
                              {app.cv_screening_results.skill_match_score}%
                            </p>
                          </div>
                        )}
                      </div>
                      {app.cv_screening_results.strengths && app.cv_screening_results.strengths.length > 0 && (
                        <div>
                          <label className="text-xs font-medium text-green-700 mb-1 block">Strengths</label>
                          <ul className="text-xs text-gray-600 list-disc list-inside">
                            {app.cv_screening_results.strengths.slice(0, 3).map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}

