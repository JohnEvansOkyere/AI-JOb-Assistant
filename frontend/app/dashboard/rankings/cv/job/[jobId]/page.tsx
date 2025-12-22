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
import { User, Mail, Trophy, Copy, Link as LinkIcon, Check, Zap, Award, Code, BookOpen, Cpu, FileText, TrendingUp, Ticket, RefreshCw } from 'lucide-react'
import { getInterviewLink, copyToClipboard } from '@/lib/utils/interview'

interface Ticket {
  id: string
  candidate_id: string
  job_description_id: string
  ticket_code: string
  created_at?: string
}

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
    // Comprehensive scores (new)
    has_detailed_screening?: boolean
    overall_score?: number
    job_match_score?: number
    experience_score?: number
    skills_score?: number
    education_score?: number
    ats_score?: number
    impact_score?: number
    format_score?: number
    structure_score?: number
    language_score?: number
    top_strengths?: string[]
    critical_issues?: string[]
    // Legacy fields (fallback)
    match_score?: number
    skill_match_score?: number
    experience_match_score?: number
    qualification_match_score?: number
    strengths?: string[]
    gaps?: string[]
    recommendation: string
    screening_notes?: string
  }
}

// Mini score bar component
function MiniScoreBar({ label, score, color = 'primary' }: { label: string; score: number; color?: string }) {
  const colorClasses: Record<string, string> = {
    primary: 'bg-primary-500',
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    yellow: 'bg-yellow-500',
  }
  
  const bgClasses: Record<string, string> = {
    primary: 'bg-primary-100',
    green: 'bg-green-100',
    blue: 'bg-blue-100',
    purple: 'bg-purple-100',
    yellow: 'bg-yellow-100',
  }

  const getScoreColor = (s: number) => {
    if (s >= 75) return 'text-green-600'
    if (s >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-600">{label}</span>
        <span className={`font-semibold ${getScoreColor(score)}`}>{Math.round(score)}%</span>
      </div>
      <div className={`h-1.5 rounded-full ${bgClasses[color]} overflow-hidden`}>
        <div 
          className={`h-full rounded-full ${colorClasses[color]} transition-all duration-300`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  )
}

export default function JobRankingsPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [candidates, setCandidates] = useState<RankedCandidate[]>([])
  const [ticketsByCandidate, setTicketsByCandidate] = useState<Record<string, Ticket>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copiedTicketCode, setCopiedTicketCode] = useState<string | null>(null)
  const [isCopiedLink, setIsCopiedLink] = useState(false)
  const [creatingTicket, setCreatingTicket] = useState<string | null>(null) // Track which candidate is getting a ticket

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
        // Fetch existing tickets for this job to know which candidates already have tickets
        // Only get unused tickets
        try {
          const ticketsResponse = await apiClient.get<Ticket[]>(`/tickets/job/${jobId}`)
          if (ticketsResponse.success && ticketsResponse.data) {
            const map: Record<string, Ticket> = {}
            // Filter to only unused tickets
            const unusedTickets = ticketsResponse.data.filter((t: any) => !t.is_used)
            unusedTickets.forEach((t) => {
              const cid = t.candidate_id
              if (!cid) return
              const existing = map[cid]
              // Prefer the most recent ticket if multiple; fall back to first
              if (!existing) {
                map[cid] = t
              } else if (t.created_at && (!existing.created_at || t.created_at > existing.created_at)) {
                map[cid] = t
              }
            })
            setTicketsByCandidate(map)
          }
        } catch (ticketErr) {
          // Don't block rankings view if tickets API fails; just log in console
          console.error('Failed to load tickets for rankings view', ticketErr)
        }
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
    if (!recommendation) return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
    if (recommendation === 'qualified') return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
    if (recommendation === 'maybe_qualified') return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300'
    return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
  }

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    if (rank === 2) return 'bg-gray-100 text-gray-800 border-gray-300'
    if (rank === 3) return 'bg-orange-100 text-orange-800 border-orange-300'
    return 'bg-blue-100 text-blue-800 border-blue-300'
  }

  const handleCopyTicketCode = async (ticketCode: string) => {
    const success = await copyToClipboard(ticketCode)
    if (success) {
      setCopiedTicketCode(ticketCode)
      setTimeout(() => setCopiedTicketCode(null), 2000)
    }
  }

  const handleCopyInterviewLink = async () => {
    const link = getInterviewLink(jobId)
    const success = await copyToClipboard(link)
    if (success) {
      setIsCopiedLink(true)
      setTimeout(() => setIsCopiedLink(false), 2000)
    }
  }

  const handleCreateTicket = async (candidateId: string) => {
    try {
      setCreatingTicket(candidateId)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      const response = await apiClient.post<{ ticket_code: string }>('/tickets', {
        candidate_id: candidateId,
        job_description_id: jobId
      })

      if (response.success && response.data) {
        // Reload rankings to get the new ticket
        await loadRankings()
      } else {
        setError(response.message || 'Failed to create ticket')
      }
    } catch (err: any) {
      console.error('Error creating ticket:', err)
      setError(err.message || 'Failed to create ticket')
    } finally {
      setCreatingTicket(null)
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">CV Rankings</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Ranked by CV screening match score (highest first)</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleCopyInterviewLink}
              className="flex items-center gap-2"
            >
              {isCopiedLink ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>Link Copied!</span>
                </>
              ) : (
                <>
                  <LinkIcon className="w-4 h-4" />
                  <span>Copy Interview Link</span>
                </>
              )}
            </Button>
            <Button variant="outline" onClick={() => router.push('/dashboard/rankings/cv')}>
              Back to CV Rankings
            </Button>
          </div>
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
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {candidate.candidates?.full_name || 'Unknown'}
                          </h3>
                          {candidate.cv_screening_results?.has_detailed_screening && (
                            <span className="text-xs px-1.5 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded">
                              Detailed
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <Mail className="w-4 h-4" />
                          <span>{candidate.candidates?.email || 'N/A'}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {candidate.cv_screening_results && (
                          <>
                            <span className={`text-xs px-2 py-1 rounded ${getRecommendationColor(candidate.cv_screening_results.recommendation)}`}>
                              {candidate.cv_screening_results.recommendation.replace('_', ' ').toUpperCase()}
                            </span>
                            <div className="text-right">
                              <div className="text-xs text-gray-500">Overall Score</div>
                              <div className="text-2xl font-bold text-primary-600">
                                {Math.round(candidate.cv_screening_results.overall_score || candidate.cv_screening_results.match_score || 0)}%
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Comprehensive Score Bars (for detailed screening) */}
                    {candidate.cv_screening_results?.has_detailed_screening && (
                      <div className="pt-3 border-t space-y-3">
                        {/* Job Match - Highlighted */}
                        <div className="flex items-center gap-3 p-2 bg-primary-50 rounded-lg">
                          <TrendingUp className="w-4 h-4 text-primary-600" />
                          <div className="flex-1">
                            <div className="flex items-center justify-between text-sm">
                              <span className="font-medium text-primary-800">Job Match</span>
                              <span className="font-bold text-primary-600">
                                {Math.round(candidate.cv_screening_results.job_match_score || 0)}%
                              </span>
                            </div>
                            <div className="h-2 bg-primary-200 rounded-full overflow-hidden mt-1">
                              <div 
                                className="h-full bg-primary-600 rounded-full"
                                style={{ width: `${candidate.cv_screening_results.job_match_score || 0}%` }}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Category Scores Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {candidate.cv_screening_results.experience_score != null && (
                            <MiniScoreBar 
                              label="Experience" 
                              score={candidate.cv_screening_results.experience_score} 
                              color="blue" 
                            />
                          )}
                          {candidate.cv_screening_results.skills_score != null && (
                            <MiniScoreBar 
                              label="Skills" 
                              score={candidate.cv_screening_results.skills_score} 
                              color="purple" 
                            />
                          )}
                          {candidate.cv_screening_results.ats_score != null && (
                            <MiniScoreBar 
                              label="ATS" 
                              score={candidate.cv_screening_results.ats_score} 
                              color="green" 
                            />
                          )}
                          {candidate.cv_screening_results.impact_score != null && (
                            <MiniScoreBar 
                              label="Impact" 
                              score={candidate.cv_screening_results.impact_score} 
                              color="yellow" 
                            />
                          )}
                        </div>
                      </div>
                    )}

                    {/* Legacy Screening Details (for basic screening) */}
                    {candidate.cv_screening_results && !candidate.cv_screening_results.has_detailed_screening && (
                      <div className="grid grid-cols-3 gap-4 pt-2 border-t">
                        {candidate.cv_screening_results.skill_match_score != null && (
                          <div>
                            <label className="text-xs font-medium text-gray-700">Skill Match</label>
                            <p className="text-sm font-semibold text-gray-900">
                              {candidate.cv_screening_results.skill_match_score}%
                            </p>
                          </div>
                        )}
                        {candidate.cv_screening_results.experience_match_score != null && (
                          <div>
                            <label className="text-xs font-medium text-gray-700">Experience Match</label>
                            <p className="text-sm font-semibold text-gray-900">
                              {candidate.cv_screening_results.experience_match_score}%
                            </p>
                          </div>
                        )}
                        {candidate.cv_screening_results.qualification_match_score != null && (
                          <div>
                            <label className="text-xs font-medium text-gray-700">Qualification Match</label>
                            <p className="text-sm font-semibold text-gray-900">
                              {candidate.cv_screening_results.qualification_match_score}%
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Top Strengths */}
                    {(candidate.cv_screening_results?.top_strengths?.length || candidate.cv_screening_results?.strengths?.length) ? (
                      <div>
                        <label className="text-xs font-medium text-green-700 mb-1 block flex items-center gap-1">
                          <Check className="w-3 h-3" /> Top Strengths
                        </label>
                        <ul className="text-xs text-gray-600 list-disc list-inside">
                          {(candidate.cv_screening_results?.top_strengths || candidate.cv_screening_results?.strengths || []).slice(0, 3).map((s, i) => (
                            <li key={i}>{s}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}

                    {/* Critical Issues (only for detailed screening) */}
                    {candidate.cv_screening_results?.critical_issues && candidate.cv_screening_results.critical_issues.length > 0 && (
                      <div>
                        <label className="text-xs font-medium text-yellow-700 mb-1 block">⚠️ Issues to Consider</label>
                        <ul className="text-xs text-gray-600 list-disc list-inside">
                          {candidate.cv_screening_results.critical_issues.slice(0, 2).map((issue, i) => (
                            <li key={i}>{issue}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2 min-w-[200px]">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/jobs/${jobId}/applications/${candidate.id}`)}
                    >
                      View Details
                    </Button>
                    {(() => {
                      // Show ticket for ALL screened candidates (tickets are auto-generated after screening)
                      const ticket = ticketsByCandidate[candidate.candidate_id]
                      if (ticket) {
                        const isCopiedCode = copiedTicketCode === ticket.ticket_code
                        return (
                          <div className="space-y-2">
                            <div className="flex items-center gap-1 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-700">
                              <Ticket className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                              <span className="text-xs font-mono text-green-800 dark:text-green-300 flex-1 truncate">
                                {ticket.ticket_code}
                              </span>
                              <button
                                onClick={() => handleCopyTicketCode(ticket.ticket_code)}
                                className="p-1 hover:bg-green-100 dark:hover:bg-green-800 rounded transition-colors"
                                title="Copy ticket code"
                              >
                                {isCopiedCode ? (
                                  <Check className="w-3 h-3 text-green-600 dark:text-green-400" />
                                ) : (
                                  <Copy className="w-3 h-3 text-green-600 dark:text-green-400" />
                                )}
                              </button>
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                              Interview ticket ready
                            </p>
                          </div>
                        )
                      }
                      // If no ticket exists but candidate has been screened, show Generate Ticket button
                      if (candidate.cv_screening_results) {
                        return (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCreateTicket(candidate.candidate_id)}
                            disabled={creatingTicket === candidate.candidate_id}
                            className="flex items-center gap-2"
                          >
                            {creatingTicket === candidate.candidate_id ? (
                              <>
                                <RefreshCw className="w-4 h-4 animate-spin" />
                                <span>Generating...</span>
                              </>
                            ) : (
                              <>
                                <Ticket className="w-4 h-4" />
                                <span>Generate Ticket</span>
                              </>
                            )}
                          </Button>
                        )
                      }
                      return null
                    })()}
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

