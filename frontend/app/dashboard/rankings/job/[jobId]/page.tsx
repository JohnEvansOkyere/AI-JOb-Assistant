/**
 * Job CV Rankings Page
 * View ranked candidates for a specific job based on CV screening, ordered by match score
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { User, Mail, Trophy, CheckCircle, Clock, XCircle } from 'lucide-react'

interface RankedCandidate {
  id: string
  rank: number
  candidate_id: string
  job_description_id: string
  status: string
  applied_at: string
  candidates?: {
    id: string
    full_name: string
    email: string
    phone?: string
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
  }
}

export default function JobRankingsPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [candidates, setCandidates] = useState<RankedCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadRankings()
    }
  }, [isAuthenticated, authLoading, router, jobId])

  const loadRankings = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.get<RankedCandidate[]>(`/rankings/cv/job/${jobId}`)
      
      if (response.success && response.data) {
        setCandidates(response.data)
      } else {
        setError(response.message || 'Failed to load rankings')
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

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    if (rank === 2) return 'bg-gray-100 text-gray-800 border-gray-300'
    if (rank === 3) return 'bg-orange-100 text-orange-800 border-orange-300'
    return 'bg-blue-100 text-blue-800 border-blue-300'
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
            <p className="text-gray-600 mt-1">Ranked by CV screening match score (highest first)</p>
          </div>
          <Button variant="outline" onClick={() => router.push('/dashboard/rankings/cv')}>
            Back to CV Rankings
          </Button>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        {candidates.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No screened candidates found for this job.</p>
              <Button variant="outline" onClick={() => router.push(`/dashboard/jobs/${jobId}/applications`)}>
                View Applications
              </Button>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {candidates.map((candidate) => (
              <Card key={candidate.id}>
                <div className="flex items-start gap-4">
                  {/* Rank Badge */}
                  <div className={`flex-shrink-0 w-16 h-16 rounded-lg border-2 flex items-center justify-center font-bold text-xl ${getRankBadgeColor(candidate.rank)}`}>
                    {candidate.rank === 1 && <Trophy className="w-6 h-6" />}
                    {candidate.rank !== 1 && `#${candidate.rank}`}
                  </div>

                  {/* Candidate Info */}
                  <div className="flex-1 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <User className="w-5 h-5 text-gray-500" />
                          <h3 className="text-lg font-semibold text-gray-900">
                            {candidate.candidates?.full_name || 'Unknown'}
                          </h3>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Mail className="w-4 h-4" />
                          <span>{candidate.candidates?.email || 'N/A'}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {candidate.cv_screening_results && (
                          <>
                            <span className={`text-xs px-2 py-1 rounded ${getRecommendationColor(candidate.cv_screening_results.recommendation)}`}>
                              {candidate.cv_screening_results.recommendation.replace('_', ' ').toUpperCase()}
                            </span>
                            <div className="text-right">
                              <div className="text-sm text-gray-600">Match Score</div>
                              <div className="text-2xl font-bold text-green-600">
                                {candidate.cv_screening_results.match_score}%
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Screening Details */}
                    {candidate.cv_screening_results && (
                      <div className="grid grid-cols-3 gap-4 pt-2 border-t">
                        {candidate.cv_screening_results.skill_match_score && (
                          <div>
                            <label className="text-xs font-medium text-gray-700">Skill Match</label>
                            <p className="text-sm font-semibold text-gray-900">
                              {candidate.cv_screening_results.skill_match_score}%
                            </p>
                          </div>
                        )}
                        {candidate.cv_screening_results.experience_match_score && (
                          <div>
                            <label className="text-xs font-medium text-gray-700">Experience Match</label>
                            <p className="text-sm font-semibold text-gray-900">
                              {candidate.cv_screening_results.experience_match_score}%
                            </p>
                          </div>
                        )}
                        {candidate.cv_screening_results.qualification_match_score && (
                          <div>
                            <label className="text-xs font-medium text-gray-700">Qualification Match</label>
                            <p className="text-sm font-semibold text-gray-900">
                              {candidate.cv_screening_results.qualification_match_score}%
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Strengths Preview */}
                    {candidate.cv_screening_results?.strengths && candidate.cv_screening_results.strengths.length > 0 && (
                      <div>
                        <label className="text-xs font-medium text-green-700 mb-1 block">Top Strengths</label>
                        <ul className="text-xs text-gray-600 list-disc list-inside">
                          {candidate.cv_screening_results.strengths.slice(0, 3).map((s, i) => (
                            <li key={i}>{s}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/jobs/${jobId}/applications/${candidate.id}`)}
                    >
                      View Details
                    </Button>
                    {candidate.cv_screening_results?.recommendation === 'qualified' && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => router.push(`/dashboard/jobs/${jobId}/applications/${candidate.id}/create-ticket`)}
                      >
                        Issue Ticket
                      </Button>
                    )}
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

