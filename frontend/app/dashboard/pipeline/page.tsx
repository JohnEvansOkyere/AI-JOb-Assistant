/**
 * Interview Pipeline Page
 * Kanban board view showing candidates across interview stages
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

interface Stage {
  id: string
  stage_number: number
  stage_name: string
  stage_type: 'ai' | 'calendar'
  is_required: boolean
  order_index: number
}

interface CandidateProgress {
  id: string
  candidate_id: string
  job_id: string
  current_stage_number: number | null
  status: string
  completed_stages: number[]
  skipped_stages: number[]
}

interface Candidate {
  id: string
  full_name: string
  email: string
}

interface CandidateWithProgress extends Candidate {
  progress?: CandidateProgress
  currentStage?: Stage
  jobTitle?: string
}

export default function PipelinePage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [selectedJobId, setSelectedJobId] = useState<string>('all')
  const [jobs, setJobs] = useState<any[]>([])
  const [stages, setStages] = useState<Stage[]>([])
  const [candidates, setCandidates] = useState<CandidateWithProgress[]>([])
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

  useEffect(() => {
    if (selectedJobId && selectedJobId !== 'all' && isAuthenticated) {
      loadStages()
      loadCandidates()
    } else if (selectedJobId === 'all' && isAuthenticated) {
      loadAllCandidates()
    }
  }, [selectedJobId, isAuthenticated])

  const loadJobs = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any[]>('/job-descriptions')
      if (response.success && response.data) {
        setJobs(response.data)
        // Auto-select first job if available
        if (response.data.length > 0 && selectedJobId === 'all') {
          setSelectedJobId(response.data[0].id)
        }
      }
    } catch (err: any) {
      console.error('Error loading jobs:', err)
      setError(ApiErrorHandler.getErrorMessage(err))
    }
  }

  const loadStages = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<Stage[]>(`/interview-stages/jobs/${selectedJobId}/stages`)
      if (response.success && response.data) {
        setStages(response.data.sort((a, b) => a.order_index - b.order_index))
      } else {
        setStages([])
      }
    } catch (err: any) {
      console.error('Error loading stages:', err)
      // Stages not configured yet - show empty state
      setStages([])
    } finally {
      setLoading(false)
    }
  }

  const loadCandidates = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      // Get applications for this job
      const applicationsResponse = await apiClient.get<any[]>(`/applications/job/${selectedJobId}`)
      
      if (applicationsResponse.success && applicationsResponse.data) {
        const applications = applicationsResponse.data
        
        // Load progress for each candidate
        const candidatesWithProgress = await Promise.all(
          applications.map(async (app) => {
            try {
              const progressResponse = await apiClient.get<CandidateProgress>(
                `/interview-stages/jobs/${selectedJobId}/candidates/${app.candidate_id}/progress`
              )
              
              const candidate: CandidateWithProgress = {
                id: app.candidate_id,
                full_name: app.candidates?.full_name || app.candidate_email || 'Unknown',
                email: app.candidates?.email || app.candidate_email || '',
                jobTitle: jobs.find(j => j.id === selectedJobId)?.title,
                progress: progressResponse.success && progressResponse.data ? progressResponse.data : undefined,
              }

              // Find current stage
              if (candidate.progress?.current_stage_number) {
                candidate.currentStage = stages.find(
                  s => s.stage_number === candidate.progress!.current_stage_number
                )
              }

              return candidate
            } catch (err) {
              // No progress yet
              const candidate: CandidateWithProgress = {
                id: app.candidate_id,
                full_name: app.candidates?.full_name || app.candidate_email || 'Unknown',
                email: app.candidates?.email || app.candidate_email || '',
                jobTitle: jobs.find(j => j.id === selectedJobId)?.title,
              }
              return candidate
            }
          })
        )

        setCandidates(candidatesWithProgress)
      }
    } catch (err: any) {
      console.error('Error loading candidates:', err)
      setError(ApiErrorHandler.getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const loadAllCandidates = async () => {
    // TODO: Load candidates from all jobs
    setCandidates([])
    setStages([])
    setLoading(false)
  }

  const getCandidatesForStage = (stageNumber: number) => {
    return candidates.filter(c => 
      c.progress?.current_stage_number === stageNumber ||
      (!c.progress && stageNumber === 1) // Place in first stage if no progress
    )
  }

  const getStageColor = (stageType: string) => {
    if (stageType === 'ai') {
      return 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700'
    }
    return 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700'
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingState message="Loading pipeline..." size="lg" />
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Interview Pipeline</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Visual view of candidates through interview stages
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Jobs</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
            
            {selectedJobId !== 'all' && (
              <Button
                variant="primary"
                onClick={() => router.push(`/dashboard/jobs/${selectedJobId}`)}
              >
                Configure Stages
              </Button>
            )}
          </div>
        </div>

        {error && (
          <ErrorDisplay
            error={error}
            onRetry={() => {
              if (selectedJobId !== 'all') {
                loadStages()
                loadCandidates()
              } else {
                loadAllCandidates()
              }
            }}
            onDismiss={() => setError('')}
            title="Failed to load pipeline"
          />
        )}

        {selectedJobId === 'all' ? (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400">
                Select a job to view its interview pipeline
              </p>
            </div>
          </Card>
        ) : stages.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                No interview stages configured for this job yet.
              </p>
              <Button
                variant="primary"
                onClick={() => router.push(`/dashboard/jobs/${selectedJobId}`)}
              >
                Configure Interview Stages
              </Button>
            </div>
          </Card>
        ) : (
          <div className="overflow-x-auto">
            <div className="flex gap-4 min-w-max pb-4">
              {stages.map((stage) => {
                const stageCandidates = getCandidatesForStage(stage.stage_number)
                return (
                  <div
                    key={stage.id}
                    className="flex-shrink-0 w-80"
                  >
                    <Card className={`${getStageColor(stage.stage_type)} border-2`}>
                      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            {stage.stage_name}
                          </h3>
                          <span className="text-xs px-2 py-1 rounded bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                            {stageCandidates.length}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded ${
                            stage.stage_type === 'ai'
                              ? 'bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200'
                              : 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200'
                          }`}>
                            {stage.stage_type === 'ai' ? 'AI Interview' : 'Human Interview'}
                          </span>
                          {stage.is_required && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              Required
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
                        {stageCandidates.length === 0 ? (
                          <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">
                            No candidates
                          </p>
                        ) : (
                          stageCandidates.map((candidate) => (
                            <div
                              key={candidate.id}
                              className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow cursor-pointer"
                              onClick={() => router.push(`/dashboard/candidates/${candidate.id}`)}
                            >
                              <p className="font-medium text-gray-900 dark:text-white">
                                {candidate.full_name || 'Unknown'}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {candidate.email}
                              </p>
                              {candidate.progress && (
                                <div className="mt-2 flex items-center gap-2">
                                  {candidate.progress.completed_stages.length > 0 && (
                                    <span className="text-xs text-green-600 dark:text-green-400">
                                      ✓ {candidate.progress.completed_stages.length} completed
                                    </span>
                                  )}
                                  {candidate.progress.status && (
                                    <span className={`text-xs px-2 py-0.5 rounded ${
                                      candidate.progress.status === 'rejected'
                                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                                        : candidate.progress.status === 'offer'
                                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                                    }`}>
                                      {candidate.progress.status}
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          ))
                        )}
                      </div>
                    </Card>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

