'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { apiClient } from '@/lib/api/client'
import { Briefcase } from 'lucide-react'

export default function JobInterviewEntryPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string
  const [ticketCode, setTicketCode] = useState('')
  const [candidateName, setCandidateName] = useState<string | null>(null)
  const [jobTitle, setJobTitle] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingJob, setLoadingJob] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load job title on mount (using public endpoint, no auth required)
  useEffect(() => {
    const loadJob = async () => {
      try {
        // Use public endpoint - candidates don't need to be authenticated
        const response = await apiClient.get<{ title?: string }>(`/public/job-descriptions/${jobId}`)
        if (response.success && response.data) {
          setJobTitle(response.data.title || null)
        }
      } catch (err) {
        console.error('Failed to load job', err)
        // Continue even if job load fails
      } finally {
        setLoadingJob(false)
      }
    }
    loadJob()
  }, [jobId])

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setCandidateName(null)

    const code = ticketCode.trim()
    if (!code) return

    try {
      setLoading(true)
      // Validate ticket before navigating
      const response = await apiClient.post<{
        valid: boolean
        ticket_id?: string
        candidate_id?: string
        job_description_id?: string
        candidate_name?: string | null
        job_title?: string | null
      }>(`/tickets/validate?ticket_code=${encodeURIComponent(code)}`)

      if (!response.success || !response.data?.valid) {
        setError(response.message || 'Invalid or expired ticket. Please check the code and try again.')
        return
      }

      // Verify the ticket is for this job
      if (response.data.job_description_id && response.data.job_description_id !== jobId) {
        setError('This ticket is not valid for this job position. Please use the correct interview link.')
        return
      }

      const name = response.data.candidate_name || null
      const title = response.data.job_title || jobTitle

      setCandidateName(name)

      // Navigate to preparation page first
      const params = new URLSearchParams()
      if (name) {
        params.set('name', name)
      }
      if (title) {
        params.set('job', title)
      }
      params.set('jobId', jobId)

      router.push(`/interview/prepare/${encodeURIComponent(code)}?${params.toString()}`)
    } catch (err: any) {
      console.error('Failed to validate ticket', err)
      setError(err.message || 'Failed to validate ticket. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <Card>
          <div className="flex items-center gap-3 mb-4">
            <Briefcase className="w-6 h-6 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Join AI Interview</h1>
              {loadingJob ? (
                <p className="text-sm text-gray-500 mt-1">Loading job details...</p>
              ) : jobTitle ? (
                <p className="text-sm text-primary-600 font-medium mt-1">{jobTitle}</p>
              ) : (
                <p className="text-sm text-gray-500 mt-1">Job Interview</p>
              )}
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Enter the interview ticket code you received from the recruiter to start your session.
          </p>
          {error && (
            <div className="mb-3 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleStart} className="space-y-4">
            <Input
              label="Ticket Code"
              type="text"
              value={ticketCode}
              onChange={(e) => setTicketCode(e.target.value)}
              placeholder="e.g., ABCD2345EFGH"
              required
            />
            <Button type="submit" variant="primary" className="w-full" disabled={loading || loadingJob}>
              {loading ? 'Checking ticket...' : 'Continue'}
            </Button>
          </form>
          {candidateName && (
            <div className="mt-4 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
              <p>
                <span className="font-medium">Candidate:</span> {candidateName}
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

