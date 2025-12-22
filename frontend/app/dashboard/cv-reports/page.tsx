'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  ExternalLink,
  Search,
  ChevronDown,
  BarChart3,
  Zap,
  RefreshCw,
  User,
  Briefcase,
  Ticket,
  Copy
} from 'lucide-react'

interface Candidate {
  id: string
  full_name: string
  email: string
  application_id: string
  has_analysis: boolean
  ticket_code?: string | null
}

interface Job {
  id: string
  title: string
}

interface CVAnalysis {
  id: string
  application_id: string
  overall_score: number
  job_match_score: number
  experience_score: number
  skills_score: number
  ats_score: number
  impact_score: number
  education_score: number
  language_score: number
  format_score: number
  structure_score: number
  recommendation: string
  recommendation_reason: string
  top_strengths: string[]
  critical_issues: string[]
  screened_at: string
}

export default function CVReportsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [jobs, setJobs] = useState<Job[]>([])
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [selectedJob, setSelectedJob] = useState<string>('')
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [analysis, setAnalysis] = useState<CVAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingCandidates, setLoadingCandidates] = useState(false)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const [creatingTicket, setCreatingTicket] = useState(false)
  const [ticketCode, setTicketCode] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadJobs()
    }
  }, [isAuthenticated, authLoading, router])

  // Load candidates when job changes
  useEffect(() => {
    if (selectedJob) {
      loadCandidatesForJob(selectedJob)
      setSelectedCandidate(null)
      setAnalysis(null)
      setSearchTerm('')
    } else {
      setCandidates([])
    }
  }, [selectedJob])

  // Load analysis when candidate changes
  useEffect(() => {
    if (selectedCandidate) {
      loadAnalysis(selectedCandidate.application_id)
      setTicketCode(null) // Reset ticket when changing candidate
    } else {
      setAnalysis(null)
      setTicketCode(null)
    }
  }, [selectedCandidate])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      const response = await apiClient.get<Job[]>('/job-descriptions')
      if (response.success && response.data) {
        setJobs(response.data)
      }
    } catch (err) {
      console.error('Error loading jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadCandidatesForJob = async (jobId: string) => {
    try {
      setLoadingCandidates(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      // Get applications for this job with candidate info
      const response = await apiClient.get<any[]>(`/applications/job/${jobId}`)
      
      if (response.success && response.data) {
        // Get all tickets for this job
        let tickets: any[] = []
        try {
          const ticketsResponse = await apiClient.get<any[]>(`/tickets/job/${jobId}`)
          if (ticketsResponse.success && ticketsResponse.data) {
            tickets = ticketsResponse.data.filter((t: any) => !t.is_used)
          }
        } catch (err) {
          console.error('Error loading tickets:', err)
        }
        
        // Check which have analysis and tickets
        const candidateList: Candidate[] = await Promise.all(
          response.data.map(async (app: any) => {
            const candidateId = app.candidates?.id || app.candidate_id
            
            // Check if analysis exists
            let hasAnalysis = false
            try {
              const analysisCheck = await apiClient.get(`/cv-screening/result/${app.id}`)
              if (analysisCheck.success) {
                const data = analysisCheck.data as any
                hasAnalysis = !!(data?.data || data?.overall_score)
              }
            } catch {}
            
            // Find ticket for this candidate
            const ticket = tickets.find(
              (t: any) => t.candidate_id === candidateId
            )
            
            return {
              id: candidateId,
              full_name: app.candidates?.full_name || 'Unknown',
              email: app.candidates?.email || '',
              application_id: app.id,
              has_analysis: hasAnalysis,
              ticket_code: ticket?.ticket_code || null
            }
          })
        )
        
        setCandidates(candidateList)
      }
    } catch (err) {
      console.error('Error loading candidates:', err)
    } finally {
      setLoadingCandidates(false)
    }
  }

  const loadAnalysis = async (applicationId: string) => {
    try {
      setLoadingAnalysis(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      const response = await apiClient.get<CVAnalysis | { data: CVAnalysis | null }>(
        `/cv-screening/result/${applicationId}`
      )

      if (response.success && response.data) {
        let analysisData: CVAnalysis | null = null
        if ('data' in response.data && response.data.data) {
          analysisData = response.data.data as CVAnalysis
        } else if ('overall_score' in response.data) {
          analysisData = response.data as CVAnalysis
        }
        setAnalysis(analysisData)
        
        // Use ticket from candidate object if available, otherwise fetch
        if (analysisData && selectedCandidate) {
          if (selectedCandidate.ticket_code) {
            setTicketCode(selectedCandidate.ticket_code)
          } else if (selectedJob) {
            await loadTicketForCandidate(selectedCandidate.id, selectedJob)
          }
        }
      }
    } catch (err) {
      console.error('Error loading analysis:', err)
      setAnalysis(null)
    } finally {
      setLoadingAnalysis(false)
    }
  }

  const loadTicketForCandidate = async (candidateId: string, jobId: string) => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      // Get all tickets for this job
      const response = await apiClient.get<any[]>(`/tickets/job/${jobId}`)
      
      if (response.success && response.data) {
        // Find ticket for this candidate that hasn't been used
        const ticket = response.data.find(
          (t: any) => t.candidate_id === candidateId && !t.is_used
        )
        
        if (ticket) {
          setTicketCode(ticket.ticket_code)
        }
      }
    } catch (err) {
      console.error('Error loading ticket:', err)
      // Silently fail - ticket might not exist yet
    }
  }

  const runAnalysis = async () => {
    if (!selectedCandidate) return
    
    try {
      setAnalyzing(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      await apiClient.post(`/cv-screening/analyze/${selectedCandidate.application_id}`)
      
      // Poll for results
      let attempts = 0
      const maxAttempts = 15
      
      const poll = async () => {
        attempts++
        try {
          const response = await apiClient.get<CVAnalysis | { data: CVAnalysis | null }>(
            `/cv-screening/result/${selectedCandidate.application_id}`
          )
          
          if (response.success && response.data) {
            let analysisData: CVAnalysis | null = null
            if ('data' in response.data && response.data.data) {
              analysisData = response.data.data as CVAnalysis
            } else if ('overall_score' in response.data) {
              analysisData = response.data as CVAnalysis
            }
            
            if (analysisData) {
              setAnalysis(analysisData)
              setAnalyzing(false)
              // Update candidate's has_analysis flag
              setCandidates(prev => prev.map(c => 
                c.application_id === selectedCandidate.application_id 
                  ? { ...c, has_analysis: true } 
                  : c
              ))
              // Automatically fetch ticket after analysis completes
              if (selectedJob) {
                await loadTicketForCandidate(selectedCandidate.id, selectedJob)
              }
              return
            }
          }
        } catch {}
        
        if (attempts < maxAttempts) {
          setTimeout(poll, 4000)
        } else {
          setAnalyzing(false)
          alert('Analysis is taking longer than expected. Please try again.')
        }
      }
      
      setTimeout(poll, 3000)
    } catch (err: any) {
      console.error('Error running analysis:', err)
      setAnalyzing(false)
      alert(err.message || 'Failed to start analysis')
    }
  }

  const createInterviewTicket = async () => {
    if (!selectedCandidate || !selectedJob) return
    
    try {
      setCreatingTicket(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      // Get candidate_id from the candidate
      const response = await apiClient.post<{ ticket_code: string }>('/tickets', {
        candidate_id: selectedCandidate.id,
        job_description_id: selectedJob
      })

      if (response.success && response.data) {
        setTicketCode((response.data as { ticket_code: string }).ticket_code)
      }
    } catch (err: any) {
      console.error('Error creating ticket:', err)
      alert(err.message || 'Failed to create ticket')
    } finally {
      setCreatingTicket(false)
    }
  }

  const copyTicket = () => {
    if (ticketCode) {
      navigator.clipboard.writeText(ticketCode)
    }
  }

  const getRecommendationConfig = (recommendation: string) => {
    const configs = {
      qualified: {
        icon: CheckCircle,
        label: 'Qualified',
        className: 'bg-green-100 text-green-800 border-green-200'
      },
      maybe_qualified: {
        icon: AlertTriangle,
        label: 'Maybe Qualified',
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
      },
      not_qualified: {
        icon: XCircle,
        label: 'Not Qualified',
        className: 'bg-red-100 text-red-800 border-red-200'
      }
    }
    return configs[recommendation as keyof typeof configs] || configs.maybe_qualified
  }

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-green-600'
    if (score >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBarColor = (score: number) => {
    if (score >= 75) return 'bg-green-500'
    if (score >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const filteredCandidates = candidates.filter(c =>
    c.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

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
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <BarChart3 className="w-7 h-7 text-primary-600" />
            CV Analysis Reports
          </h1>
          <p className="text-gray-600 mt-1">
            Select a job and candidate to view or run detailed CV analysis
          </p>
        </div>

        {/* Selection Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Job Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Briefcase className="w-4 h-4 inline mr-2" />
              Select Job
            </label>
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
            >
              <option value="">-- Select a Job --</option>
              {jobs.map(job => (
                <option key={job.id} value={job.id}>{job.title}</option>
              ))}
            </select>
          </div>

          {/* Candidate Selection */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Select Candidate
            </label>
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder={selectedJob ? "Search or select candidate..." : "Select a job first"}
                  value={selectedCandidate ? selectedCandidate.full_name : searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value)
                    setSelectedCandidate(null)
                    setShowDropdown(true)
                  }}
                  onFocus={() => setShowDropdown(true)}
                  disabled={!selectedJob}
                  className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              </div>

              {/* Dropdown */}
              {showDropdown && selectedJob && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {loadingCandidates ? (
                    <div className="p-4 text-center text-gray-500">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
                      Loading candidates...
                    </div>
                  ) : filteredCandidates.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      No candidates found
                    </div>
                  ) : (
                    filteredCandidates.map(candidate => (
                      <button
                        key={candidate.application_id}
                        onClick={() => {
                          setSelectedCandidate(candidate)
                          setSearchTerm('')
                          setShowDropdown(false)
                        }}
                        className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between border-b border-gray-100 last:border-b-0"
                      >
                        <div>
                          <div className="font-medium text-gray-900">{candidate.full_name}</div>
                          <div className="text-sm text-gray-500">{candidate.email}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          {candidate.has_analysis && (
                            <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                              ✓ Analyzed
                            </span>
                          )}
                          {candidate.ticket_code && (
                            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full flex items-center gap-1">
                              <Ticket className="w-3 h-3" />
                              Ticket Ready
                            </span>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Click outside to close dropdown */}
        {showDropdown && (
          <div 
            className="fixed inset-0 z-0" 
            onClick={() => setShowDropdown(false)}
          />
        )}

        {/* Analysis Section */}
        {selectedCandidate && (
          <Card className="mt-6">
            {/* Candidate Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                  <User className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selectedCandidate.full_name}</h2>
                  <p className="text-gray-600">{selectedCandidate.email}</p>
                </div>
              </div>

              <div className="flex gap-3 flex-wrap">
                <Button
                  variant="outline"
                  onClick={runAnalysis}
                  disabled={analyzing}
                >
                  {analyzing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      {analysis ? 'Re-analyze' : 'Run Analysis'}
                    </>
                  )}
                </Button>

                {/* Ticket Display - Show for all screened candidates */}
                {analysis && (
                  !ticketCode && !selectedCandidate?.ticket_code ? (
                    <Button
                      variant="outline"
                      onClick={createInterviewTicket}
                      disabled={creatingTicket}
                      title="Create interview ticket for this screened candidate (ticket should be auto-generated after screening)"
                    >
                      {creatingTicket ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <Ticket className="w-4 h-4 mr-2" />
                          Generate Ticket
                        </>
                      )}
                    </Button>
                  ) : (
                    <div className="flex items-center gap-2 bg-green-100 dark:bg-green-900/30 px-3 py-2 rounded-lg border border-green-200 dark:border-green-700">
                      <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="font-mono font-bold text-green-800 dark:text-green-300">
                        {ticketCode || selectedCandidate?.ticket_code}
                      </span>
                      <button 
                        onClick={() => {
                          const code = ticketCode || selectedCandidate?.ticket_code
                          if (code) {
                            navigator.clipboard.writeText(code)
                            alert('Ticket code copied!')
                          }
                        }}
                        className="p-1 hover:bg-green-200 dark:hover:bg-green-800 rounded"
                        title="Copy ticket code"
                      >
                        <Copy className="w-4 h-4 text-green-600 dark:text-green-400" />
                      </button>
                    </div>
                  )
                )}
                
                {analysis && (
                  <Button
                    variant="primary"
                    onClick={() => router.push(`/cv-report/${selectedCandidate.application_id}`)}
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Full Report
                  </Button>
                )}
              </div>
            </div>

            {/* Analysis Content */}
            {loadingAnalysis ? (
              <div className="py-12 text-center">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto text-primary-600 mb-4" />
                <p className="text-gray-600">Loading analysis...</p>
              </div>
            ) : analyzing ? (
              <div className="py-12 text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-200 border-t-primary-600 mx-auto mb-4"></div>
                <p className="text-lg font-medium text-gray-900">Analyzing CV...</p>
                <p className="text-gray-600 mt-1">This may take 20-30 seconds</p>
              </div>
            ) : analysis ? (
              <div className="space-y-6">
                {/* Score Summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-xl">
                    <div className={`text-4xl font-bold ${getScoreColor(analysis.overall_score)}`}>
                      {Math.round(analysis.overall_score)}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Overall Score</div>
                  </div>
                  <div className="text-center p-4 bg-primary-50 rounded-xl">
                    <div className={`text-4xl font-bold ${getScoreColor(analysis.job_match_score)}`}>
                      {Math.round(analysis.job_match_score)}%
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Job Match</div>
                  </div>
                  <div className="col-span-2 flex items-center justify-center p-4">
                    {(() => {
                      const config = getRecommendationConfig(analysis.recommendation)
                      const Icon = config.icon
                      return (
                        <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-full border ${config.className}`}>
                          <Icon className="w-6 h-6" />
                          <span className="text-lg font-bold">{config.label}</span>
                        </div>
                      )
                    })()}
                  </div>
                </div>

                {/* Category Scores */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Experience', score: analysis.experience_score },
                    { label: 'Skills', score: analysis.skills_score },
                    { label: 'ATS', score: analysis.ats_score },
                    { label: 'Impact', score: analysis.impact_score },
                    { label: 'Education', score: analysis.education_score },
                    { label: 'Language', score: analysis.language_score },
                    { label: 'Format', score: analysis.format_score },
                    { label: 'Structure', score: analysis.structure_score },
                  ].map(item => (
                    <div key={item.label} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">{item.label}</span>
                        <span className={`font-bold ${getScoreColor(item.score)}`}>
                          {Math.round(item.score)}%
                        </span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${getScoreBarColor(item.score)}`}
                          style={{ width: `${item.score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Strengths & Issues */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {analysis.top_strengths && analysis.top_strengths.length > 0 && (
                    <div className="p-4 bg-green-50 rounded-xl border border-green-200">
                      <h3 className="font-bold text-green-800 mb-3 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        Top Strengths
                      </h3>
                      <ul className="space-y-2">
                        {analysis.top_strengths.slice(0, 5).map((s, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-green-700">
                            <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysis.critical_issues && analysis.critical_issues.length > 0 && (
                    <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
                      <h3 className="font-bold text-yellow-800 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5" />
                        Areas to Consider
                      </h3>
                      <ul className="space-y-2">
                        {analysis.critical_issues.slice(0, 5).map((s, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-yellow-700">
                            <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="text-center text-sm text-gray-500 pt-4 border-t">
                  Analyzed: {new Date(analysis.screened_at).toLocaleString()}
                </div>
              </div>
            ) : (
              /* No Analysis Yet */
              <div className="py-12 text-center">
                <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analysis Yet</h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Run a detailed CV analysis to get insights on this candidate&apos;s qualifications, 
                  skills match, and hiring recommendation.
                </p>
                <Button
                  variant="primary"
                  size="lg"
                  onClick={runAnalysis}
                  disabled={analyzing}
                >
                  <Zap className="w-5 h-5 mr-2" />
                  Run Detailed Analysis
                </Button>
              </div>
            )}
          </Card>
        )}

        {/* Empty State - No Selection */}
        {!selectedJob && (
          <Card className="py-16 text-center">
            <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Select a Job to Start</h3>
            <p className="text-gray-600">
              Choose a job from the dropdown above to see candidates and their CV analyses.
            </p>
          </Card>
        )}

        {selectedJob && !selectedCandidate && !loadingCandidates && (
          <Card className="py-16 text-center">
            <User className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Select a Candidate</h3>
            <p className="text-gray-600">
              {candidates.length > 0 
                ? `${candidates.length} candidate${candidates.length !== 1 ? 's' : ''} found. Click the search box to select one.`
                : 'No candidates have applied for this job yet.'}
            </p>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
