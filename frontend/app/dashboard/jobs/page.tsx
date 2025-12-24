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
import { Check, Copy, ChevronDown, Mail, CheckCircle2 } from 'lucide-react'

export default function JobsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [jobs, setJobs] = useState<JobDescription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copiedJobId, setCopiedJobId] = useState<string | null>(null)
  const [updatingHiringStatus, setUpdatingHiringStatus] = useState<string | null>(null)
  const [sendingRejections, setSendingRejections] = useState<string | null>(null)
  const [showCompleteHiringModal, setShowCompleteHiringModal] = useState<string | null>(null)
  const [selectedHiringStatus, setSelectedHiringStatus] = useState<'filled' | 'closed'>('filled')

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

  const handleHiringStatusChange = async (jobId: string, newStatus: 'active' | 'screening' | 'interviewing' | 'filled' | 'closed') => {
    try {
      setUpdatingHiringStatus(jobId)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.put<JobDescription>(
        `/job-descriptions/${jobId}`,
        { hiring_status: newStatus }
      )
      
      if (response.success && response.data) {
        setJobs(prevJobs => 
          prevJobs.map(job => 
            job.id === jobId 
              ? { ...job, hiring_status: response.data!.hiring_status }
              : job
          )
        )
      } else {
        setError(response.message || 'Failed to update hiring status')
      }
    } catch (err: any) {
      console.error('Error updating hiring status:', err)
      const errorMessage = ApiErrorHandler.getErrorMessage(err)
      setError(errorMessage)
    } finally {
      setUpdatingHiringStatus(null)
    }
  }

  const handleCompleteHiring = async (jobId: string, sendRejections: boolean = false) => {
    try {
      setUpdatingHiringStatus(jobId)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      // Update hiring status
      const statusResponse = await apiClient.post<JobDescription>(
        `/job-descriptions/${jobId}/complete-hiring`,
        { hiring_status: selectedHiringStatus }
      )
      
      if (statusResponse.success && statusResponse.data) {
        setJobs(prevJobs => 
          prevJobs.map(job => 
            job.id === jobId 
              ? { ...job, hiring_status: statusResponse.data!.hiring_status }
              : job
          )
        )
        
        // Send rejection emails if requested
        if (sendRejections) {
          setSendingRejections(jobId)
          try {
            const rejectionsResponse = await apiClient.post<{ cv_rejections_sent: number; interview_rejections_sent: number }>(
              `/job-descriptions/${jobId}/send-rejections`
            )
            
            if (rejectionsResponse.success) {
              alert(`Hiring completed! ${rejectionsResponse.data?.cv_rejections_sent || 0} CV rejections and ${rejectionsResponse.data?.interview_rejections_sent || 0} interview rejections sent.`)
            }
          } catch (err: any) {
            console.error('Error sending rejections:', err)
            const errorMessage = ApiErrorHandler.getErrorMessage(err)
            alert(`Hiring status updated, but failed to send rejections: ${errorMessage}`)
          } finally {
            setSendingRejections(null)
          }
        }
        
        setShowCompleteHiringModal(null)
      } else {
        setError(statusResponse.message || 'Failed to complete hiring')
      }
    } catch (err: any) {
      console.error('Error completing hiring:', err)
      const errorMessage = ApiErrorHandler.getErrorMessage(err)
      setError(errorMessage)
    } finally {
      setUpdatingHiringStatus(null)
    }
  }

  const handleSendRejections = async (jobId: string) => {
    try {
      setSendingRejections(jobId)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      const response = await apiClient.post<{ cv_rejections_sent: number; interview_rejections_sent: number }>(
        `/job-descriptions/${jobId}/send-rejections`
      )
      
      if (response.success && response.data) {
        alert(`Rejection emails sent! ${response.data.cv_rejections_sent} CV rejections and ${response.data.interview_rejections_sent} interview rejections.`)
      } else {
        setError(response.message || 'Failed to send rejection emails')
      }
    } catch (err: any) {
      console.error('Error sending rejections:', err)
      const errorMessage = ApiErrorHandler.getErrorMessage(err)
      setError(errorMessage)
    } finally {
      setSendingRejections(null)
    }
  }

  const getHiringStatusColor = (status?: string) => {
    switch (status) {
      case 'active':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-700'
      case 'screening':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700'
      case 'interviewing':
        return 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 border-purple-300 dark:border-purple-700'
      case 'filled':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-300 dark:border-green-700'
      case 'closed':
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 border-gray-300 dark:border-gray-600'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 border-gray-300 dark:border-gray-600'
    }
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Job Descriptions</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Create and manage your job postings</p>
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
              <p className="text-gray-600 dark:text-gray-400 mb-4">No job descriptions yet.</p>
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
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">{job.description}</p>
                  {job.location && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">📍 {job.location}</p>
                  )}
                  {job.experience_level && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">Level: {job.experience_level}</p>
                  )}
                  <div className="space-y-2 pt-2">
                    {/* Hiring Status */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="relative flex-1">
                        <select
                          value={job.hiring_status || 'active'}
                          onChange={(e) => {
                            const newStatus = e.target.value as 'active' | 'screening' | 'interviewing' | 'filled' | 'closed'
                            handleHiringStatusChange(job.id, newStatus)
                          }}
                          disabled={updatingHiringStatus === job.id}
                          className={`w-full text-xs px-3 py-1.5 pr-8 rounded border appearance-none cursor-pointer transition-colors font-medium ${getHiringStatusColor(job.hiring_status)} ${updatingHiringStatus === job.id ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-primary-500'}`}
                        >
                          <option value="active">📋 Active</option>
                          <option value="screening">🔍 Screening</option>
                          <option value="interviewing">💼 Interviewing</option>
                          <option value="filled">✅ Filled</option>
                          <option value="closed">❌ Closed</option>
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none opacity-60" />
                      </div>
                      {updatingHiringStatus === job.id && (
                        <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">Updating...</span>
                      )}
                    </div>

                    {/* Action Buttons */}
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

                    {/* Complete Hiring & Send Rejections */}
                    {(job.hiring_status === 'filled' || job.hiring_status === 'closed') ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSendRejections(job.id)}
                        disabled={sendingRejections === job.id}
                        className="w-full flex items-center justify-center gap-2 text-orange-600 dark:text-orange-400 border-orange-300 dark:border-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/20"
                      >
                        <Mail className="w-3 h-3" />
                        {sendingRejections === job.id ? 'Sending...' : 'Send Rejection Emails'}
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedHiringStatus('filled')
                          setShowCompleteHiringModal(job.id)
                        }}
                        className="w-full flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400 border-blue-300 dark:border-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        Complete Hiring
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Complete Hiring Modal */}
        {showCompleteHiringModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Complete Hiring Process</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Final Status
                  </label>
                  <select
                    value={selectedHiringStatus}
                    onChange={(e) => setSelectedHiringStatus(e.target.value as 'filled' | 'closed')}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="filled">✅ Filled (Position has been filled)</option>
                    <option value="closed">❌ Closed (Position closed, not filled)</option>
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="sendRejections"
                    defaultChecked={true}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label htmlFor="sendRejections" className="text-sm text-gray-700 dark:text-gray-300">
                    Send rejection emails to candidates who didn't make it
                  </label>
                </div>
                <div className="flex gap-2 justify-end pt-4">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowCompleteHiringModal(null)
                      setSelectedHiringStatus('filled')
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => {
                      const sendRejections = (document.getElementById('sendRejections') as HTMLInputElement)?.checked || false
                      handleCompleteHiring(showCompleteHiringModal, sendRejections)
                    }}
                    disabled={updatingHiringStatus === showCompleteHiringModal}
                  >
                    {updatingHiringStatus === showCompleteHiringModal ? 'Processing...' : 'Complete Hiring'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
