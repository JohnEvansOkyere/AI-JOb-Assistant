'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/lib/api/client'
import { Wifi, Shield, Volume2, Clock, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react'

export default function InterviewPreparationPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const ticketCode = params.ticketCode as string
  
  const [candidateName, setCandidateName] = useState<string | null>(null)
  const [jobTitle, setJobTitle] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Get candidate name and job title from URL params or validate ticket
  useEffect(() => {
    const name = searchParams.get('name')
    const job = searchParams.get('job')
    
    if (name && job) {
      setCandidateName(name)
      setJobTitle(job)
      setLoading(false)
    } else {
      // Validate ticket to get candidate info
      validateTicket()
    }
  }, [ticketCode, searchParams])

  const validateTicket = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.post<{
        valid: boolean
        candidate_name?: string | null
        job_title?: string | null
      }>(`/tickets/validate?ticket_code=${encodeURIComponent(ticketCode)}`)

      if (!response.success || !response.data?.valid) {
        setError(response.message || 'Invalid or expired ticket.')
        return
      }

      setCandidateName(response.data.candidate_name || null)
      setJobTitle(response.data.job_title || null)
    } catch (err: any) {
      console.error('Failed to validate ticket', err)
      setError(err.message || 'Failed to validate ticket.')
    } finally {
      setLoading(false)
    }
  }

  const handleStartInterview = () => {
    // Navigate to interview page with candidate info
    const params = new URLSearchParams()
    if (candidateName) {
      params.set('name', candidateName)
    }
    if (jobTitle) {
      params.set('job', jobTitle)
    }
    router.push(`/interview/${encodeURIComponent(ticketCode)}${params.toString() ? `?${params.toString()}` : ''}`)
  }

  const handleCancel = () => {
    // Go back to entry page - ticket remains valid
    const jobId = searchParams.get('jobId')
    if (jobId) {
      router.push(`/interview/job/${jobId}`)
    } else {
      router.push('/interview')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center px-4">
        <Card>
          <div className="text-center py-8">
            <div className="text-red-600 mb-4">
              <Shield className="w-16 h-16 mx-auto" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Unable to Proceed</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button variant="primary" onClick={handleCancel}>
              Go Back
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full">
        <Card className="shadow-xl">
          <div className="p-8 space-y-6">
            {/* Welcome Header */}
            <div className="text-center space-y-3">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-4">
                <CheckCircle className="w-8 h-8 text-primary-600" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900">
                {candidateName ? `Welcome, ${candidateName}!` : 'Welcome!'}
              </h1>
              {jobTitle && (
                <p className="text-lg text-primary-600 font-medium">
                  Interview for: {jobTitle}
                </p>
              )}
              <p className="text-gray-600 text-base">
                We're excited to learn more about you! Before we begin, let's make sure you're all set for a great interview experience.
              </p>
            </div>

            {/* Encouragement Section */}
            <div className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-lg p-6 border border-primary-100">
              <p className="text-gray-700 text-center leading-relaxed">
                <span className="font-semibold text-primary-700">Take a deep breath!</span> This is your opportunity to showcase your skills and experience. 
                We're here to have a meaningful conversation and get to know you better. There's no need to be nervous—just be yourself and share your story.
              </p>
            </div>

            {/* Important Notes */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <Shield className="w-6 h-6 text-primary-600" />
                Things to Note
              </h2>
              
              <div className="space-y-4">
                {/* Network Check */}
                <div className="flex items-start gap-4 p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 transition-colors">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <Wifi className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">1. Ensure Your Network is Strong</h3>
                    <p className="text-sm text-gray-600">
                      A stable internet connection is essential for a smooth interview experience. Please check your connection before starting.
                    </p>
                  </div>
                </div>

                {/* Interview Continuity */}
                <div className="flex items-start gap-4 p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 transition-colors">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-amber-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">2. Interview Cannot Be Stopped Once Begun</h3>
                    <p className="text-sm text-gray-600">
                      Once you click "Start Interview", the session will begin and cannot be paused. Make sure you're ready and won't be interrupted.
                    </p>
                  </div>
                </div>

                {/* Quiet Environment */}
                <div className="flex items-start gap-4 p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 transition-colors">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                    <Volume2 className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">3. Find a Quiet Environment</h3>
                    <p className="text-sm text-gray-600">
                      Choose a quiet, comfortable space where you can focus and won't be disturbed. This will help you give your best performance.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Final Encouragement */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 border border-green-200">
              <p className="text-gray-700 text-center leading-relaxed">
                <span className="font-semibold text-green-700">You've got this!</span> When you feel confident and ready, 
                click the button below to begin your interview. We're looking forward to hearing from you.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button
                variant="outline"
                onClick={handleCancel}
                className="flex-1 flex items-center justify-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Come Back Later
              </Button>
              <Button
                variant="primary"
                onClick={handleStartInterview}
                className="flex-1 flex items-center justify-center gap-2 text-lg py-3"
              >
                Start Interview
                <ArrowRight className="w-5 h-5" />
              </Button>
            </div>

            {/* Reassurance Footer */}
            <p className="text-xs text-gray-500 text-center pt-2">
              Don't worry—if you need to step away, you can come back later. Your ticket will remain valid until you complete the interview.
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}

