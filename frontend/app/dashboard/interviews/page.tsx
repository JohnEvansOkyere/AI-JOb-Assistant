/**
 * Interviews Page
 * View and manage interview sessions
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiClient } from '@/lib/api/client'
import { CheckCircle, XCircle, Mail, Filter } from 'lucide-react'

interface InterviewRow {
  id: string
  status: string
  job_status?: string | null
  created_at: string
  job_description_id: string
  job_title?: string | null
  candidate?: {
    id: string
    full_name?: string | null
    email?: string | null
  } | null
  report?: {
    skill_match_score?: number | null
    hiring_recommendation?: string | null
    strengths?: string[] | null
    weaknesses?: string[] | null
    red_flags?: string[] | null
    experience_level?: string | null
    recommendation_justification?: string | null
    recruiter_notes?: string | null
    created_at?: string
  } | null
}

interface Job {
  id: string
  title: string
}

export default function InterviewsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [interviews, setInterviews] = useState<InterviewRow[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJobId, setSelectedJobId] = useState<string>('')
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null)
  const [bulkSending, setBulkSending] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }
    if (!authLoading && isAuthenticated) {
      loadInterviews()
      loadJobs()
    }
  }, [isAuthenticated, authLoading, router])

  const loadInterviews = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.get<InterviewRow[]>('/interviews')
      if (response.success && Array.isArray(response.data)) {
        setInterviews(response.data)
      } else {
        setError(response.message || 'Failed to load interviews')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load interviews')
    } finally {
      setLoading(false)
    }
  }

  const loadJobs = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any>('/job-descriptions')
      if (response.success && response.data) {
        const jobsList = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data?.data) ? response.data.data : [])
        setJobs(jobsList)
      }
    } catch (err: any) {
      console.error('Error loading jobs:', err)
    }
  }

  const updateJobStatus = async (interviewId: string, jobStatus: string) => {
    try {
      setUpdatingStatus(interviewId)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.put(`/interviews/${interviewId}/job-status`, {
        job_status: jobStatus
      })

      if (response.success) {
        // Reload interviews to get updated status
        await loadInterviews()
      } else {
        alert('Failed to update status: ' + response.message)
      }
    } catch (err: any) {
      alert('Error: ' + (err.message || 'Unknown error'))
    } finally {
      setUpdatingStatus(null)
    }
  }

  const handleBulkSendEmails = async (jobStatus: 'accepted' | 'rejected') => {
    if (!selectedJobId) {
      alert('Please select a job first')
      return
    }

    if (!confirm(`Send ${jobStatus} emails to all ${jobStatus} candidates for this job?`)) {
      return
    }

    try {
      setBulkSending(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const templateType = jobStatus === 'accepted' ? 'acceptance' : 'rejection'

      // Response from bulk-send contains e.g. { sent_count: number }
      type BulkSendResponse = { sent_count?: number }

      const response = await apiClient.post<BulkSendResponse>('/emails/bulk-send', {
        job_description_id: selectedJobId,
        job_status: jobStatus,
        template_type: templateType
      })

      if (response.success) {
        const sentCount = (response.data && (response.data as BulkSendResponse).sent_count) || 0
        alert(`Bulk email sending initiated for ${sentCount} candidates`)
      } else {
        alert('Failed to send bulk emails: ' + response.message)
      }
    } catch (err: any) {
      alert('Error: ' + (err.message || 'Unknown error'))
    } finally {
      setBulkSending(false)
    }
  }

  const getJobStatusBadge = (jobStatus?: string | null) => {
    if (!jobStatus) return null
    
    const statusConfig: Record<string, { color: string; label: string }> = {
      accepted: { color: 'bg-green-100 text-green-700', label: 'Accepted' },
      rejected: { color: 'bg-red-100 text-red-700', label: 'Rejected' },
      under_review: { color: 'bg-yellow-100 text-yellow-700', label: 'Under Review' },
      pending: { color: 'bg-gray-100 text-gray-700', label: 'Pending' },
    }
    
    const config = statusConfig[jobStatus] || statusConfig.pending
    return (
      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    )
  }

  const filteredInterviews = selectedJobId
    ? interviews.filter(i => i.job_description_id === selectedJobId)
    : interviews

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading interviews...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const hasData = interviews.length > 0

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Interviews</h1>
            <p className="text-gray-600 mt-1">Monitor interview sessions and AI insights.</p>
          </div>
        </div>

        {/* Filters and Bulk Actions */}
        <Card>
          <div className="p-4 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <label className="text-sm font-medium text-gray-700">Filter by Job:</label>
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Jobs</option>
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title}
                  </option>
                ))}
              </select>
            </div>
            
            {selectedJobId && (
              <div className="flex items-center gap-2 ml-auto">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkSendEmails('accepted')}
                  loading={bulkSending}
                  disabled={bulkSending}
                >
                  <Mail className="w-4 h-4 mr-2" />
                  Send Acceptance Emails
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkSendEmails('rejected')}
                  loading={bulkSending}
                  disabled={bulkSending}
                >
                  <Mail className="w-4 h-4 mr-2" />
                  Send Rejection Emails
                </Button>
              </div>
            )}
          </div>
        </Card>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        <Card>
          {filteredInterviews.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-2">No interviews yet.</p>
              <p className="text-sm text-gray-500 mb-4">
                Once candidates complete AI interviews, you&apos;ll see their sessions and AI summaries
                here.
              </p>
              <Button variant="outline" onClick={() => router.push('/dashboard')}>
                Back to Dashboard
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs font-semibold text-gray-500 uppercase">
                    <th className="py-3 pr-4">Candidate</th>
                    <th className="py-3 pr-4">Job</th>
                    <th className="py-3 pr-4">Interview Status</th>
                    <th className="py-3 pr-4">Job Status</th>
                    <th className="py-3 pr-4">Actions</th>
                    <th className="py-3 pr-4">Skill Match</th>
                    <th className="py-3 pr-4">Recommendation</th>
                    <th className="py-3 pr-4">Key Strengths</th>
                    <th className="py-3 pr-4">Key Weaknesses</th>
                    <th className="py-3 pr-4">Red Flags</th>
                    <th className="py-3 pr-4">Experience</th>
                    <th className="py-3 pr-4">Report Summary</th>
                    <th className="py-3 pr-4">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInterviews.map((i) => {
                    const rec = i.report?.hiring_recommendation || 'neutral'
                    const recColor =
                      rec === 'no_hire'
                        ? 'bg-red-100 text-red-700'
                        : rec === 'hire' || rec === 'strong_hire'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'

                    return (
                      <tr key={i.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 pr-4">
                          <div className="font-medium text-gray-900">
                            {i.candidate?.full_name || 'Unknown'}
                          </div>
                          <div className="text-xs text-gray-500">{i.candidate?.email}</div>
                        </td>
                        <td className="py-3 pr-4 text-gray-900">{i.job_title || '—'}</td>
                        <td className="py-3 pr-4 text-xs capitalize text-gray-700">{i.status}</td>
                        <td className="py-3 pr-4">
                          {getJobStatusBadge(i.job_status)}
                        </td>
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => updateJobStatus(i.id, 'accepted')}
                              loading={updatingStatus === i.id}
                              disabled={updatingStatus !== null}
                              className="text-green-700 border-green-300 hover:bg-green-50"
                            >
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Accept
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => updateJobStatus(i.id, 'rejected')}
                              loading={updatingStatus === i.id}
                              disabled={updatingStatus !== null}
                              className="text-red-700 border-red-300 hover:bg-red-50"
                            >
                              <XCircle className="w-3 h-3 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-gray-900">
                          {i.report?.skill_match_score != null
                            ? `${Number(i.report.skill_match_score).toFixed(1)}%`
                            : '—'}
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${recColor}`}>
                            {rec.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-xs text-gray-700 max-w-xs">
                          {i.report?.strengths && i.report.strengths.length > 0
                            ? i.report.strengths.slice(0, 2).join('; ')
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-amber-700 max-w-xs">
                          {i.report?.weaknesses && i.report.weaknesses.length > 0
                            ? i.report.weaknesses.slice(0, 2).join('; ')
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-red-700 max-w-xs">
                          {i.report?.red_flags && i.report.red_flags.length > 0
                            ? i.report.red_flags.slice(0, 2).join('; ')
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs capitalize text-gray-700">
                          {i.report?.experience_level || '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-gray-700 max-w-xs">
                          {i.report?.recommendation_justification
                            ? i.report.recommendation_justification
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-gray-500">
                          {i.created_at ? new Date(i.created_at).toLocaleString() : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}
