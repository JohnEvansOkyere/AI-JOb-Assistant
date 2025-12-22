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
  const [companyName, setCompanyName] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Get candidate name and job title from URL params or validate ticket
  useEffect(() => {
    const name = searchParams.get('name')
    const job = searchParams.get('job')
    const company = searchParams.get('company')
    
    if (name && job) {
      setCandidateName(name)
      setJobTitle(job)
      if (company) {
        setCompanyName(company)
      }
      // Always validate ticket to get company name (even if URL params are present)
      // This ensures company name is always fetched from the backend
      validateTicket()
    } else {
      // Validate ticket to get candidate info
      validateTicket()
    }
  }, [ticketCode, searchParams])

  const validateTicket = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.post<any>(`/tickets/validate?ticket_code=${encodeURIComponent(ticketCode)}`)

      if (!response.success) {
        setError(response.message || 'Invalid or expired ticket.')
        return
      }

      // Extract data - response.data contains the ticket data directly
      const ticketData = response.data as any
      
      if (!ticketData?.valid) {
        setError('Invalid or expired ticket.')
        return
      }
      
      // Update state (don't overwrite if URL params already set them, except for company_name which we always want from backend)
      if (!candidateName) {
        setCandidateName(ticketData.candidate_name || null)
      }
      if (!jobTitle) {
        setJobTitle(ticketData.job_title || null)
      }
      // Always set company name from backend (most reliable source)
      setCompanyName(ticketData.company_name || null)
      
      // Debug log
      console.log('Ticket validation response:', {
        responseSuccess: response.success,
        responseData: response.data,
        ticketData: ticketData,
        candidate_name: ticketData.candidate_name,
        job_title: ticketData.job_title,
        company_name: ticketData.company_name,
        stateAfter: { candidateName, jobTitle, companyName: ticketData.company_name }
      })
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center px-4">
        <Card>
          <div className="text-center py-8">
            <div className="text-red-600 dark:text-red-400 mb-4">
              <Shield className="w-16 h-16 mx-auto" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Unable to Proceed</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
            <Button variant="primary" onClick={handleCancel}>
              Go Back
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full">
        <Card className="shadow-xl dark:shadow-2xl">
          <div className="p-8 space-y-6">
            {/* Welcome Header */}
            <div className="text-center space-y-3">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-4">
                <CheckCircle className="w-8 h-8 text-primary-600" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                {candidateName ? (
                  <>
                    Welcome, {candidateName}!
                    {companyName && (
                      <span className="block text-xl text-primary-600 dark:text-primary-400 font-medium mt-2">
                        {companyName} AI Interview
                      </span>
                    )}
                  </>
                ) : 'Welcome!'}
              </h1>
              {jobTitle && (
                <p className="text-lg text-primary-600 dark:text-primary-400 font-medium">
                  Interview for: {jobTitle}
                </p>
              )}
              <p className="text-gray-600 dark:text-gray-300 text-base">
                We're excited to learn more about you! Before we begin, let's make sure you're all set for a great interview experience.
              </p>
            </div>

            {/* Encouragement Section */}
            <div className="bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 rounded-lg p-6 border border-primary-100 dark:border-primary-800">
              <p className="text-gray-700 dark:text-gray-300 text-center leading-relaxed">
                <span className="font-semibold text-primary-700 dark:text-primary-400">Take a deep breath!</span> This is your opportunity to showcase your skills and experience. 
                We're here to have a meaningful conversation and get to know you better. There's no need to be nervous—just be yourself and share your story.
              </p>
            </div>

            {/* Important Notes */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Shield className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                Things to Note
              </h2>
              
              <div className="space-y-4">
                {/* Network Check */}
                <div className="flex items-start gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 transition-colors">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <Wifi className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">1. Ensure Your Network is Strong</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      A stable internet connection is essential for a smooth interview experience. Please check your connection before starting.
                    </p>
                  </div>
                </div>

                {/* Interview Continuity */}
                <div className="flex items-start gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 transition-colors">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">2. Interview Cannot Be Stopped Once Begun</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      Once you click "Start Interview", the session will begin and cannot be paused. Make sure you're ready and won't be interrupted.
                    </p>
                  </div>
                </div>

                {/* Quiet Environment */}
                <div className="flex items-start gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 transition-colors">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                    <Volume2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">3. Find a Quiet Environment</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      Choose a quiet, comfortable space where you can focus and won't be disturbed. This will help you give your best performance.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Final Encouragement */}
            <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-lg p-6 border border-green-200 dark:border-green-800">
              <p className="text-gray-700 dark:text-gray-300 text-center leading-relaxed">
                <span className="font-semibold text-green-700 dark:text-green-400">You've got this!</span> When you feel confident and ready, 
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
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center pt-2">
              Don't worry—if you need to step away, you can come back later. Your ticket will remain valid until you complete the interview.
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}

