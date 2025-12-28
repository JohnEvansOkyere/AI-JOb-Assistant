/**
 * Create Interview Ticket Page
 * Create interview ticket for a qualified candidate
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Copy, Link as LinkIcon, Check, Mail, Send, Mic, Type } from 'lucide-react'
import { getInterviewLink, copyToClipboard } from '@/lib/utils/interview'

interface Application {
  id: string
  candidate_id: string
  candidates?: { full_name: string; email: string }
}

export default function CreateTicketPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string
  const applicationId = params.applicationId as string
  const { isAuthenticated, loading: authLoading } = useAuth()
  
  const [application, setApplication] = useState<Application | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [sendingEmail, setSendingEmail] = useState(false)
  const [error, setError] = useState('')
  const [ticketCode, setTicketCode] = useState('')
  const [ticketId, setTicketId] = useState<string>('')
  const [expiresInHours, setExpiresInHours] = useState(48)
  const [jobInterviewMode, setJobInterviewMode] = useState<'text' | 'voice' | null>(null)
  const [copiedCode, setCopiedCode] = useState(false)
  const [copiedLink, setCopiedLink] = useState(false)
  const [emailSent, setEmailSent] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadApplication()
    }
  }, [isAuthenticated, authLoading, router])

  const loadApplication = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      // We'll get application details from the applications list
      // For now, we'll create ticket directly
      setLoading(false)
    } catch (err: any) {
      setError(err.message || 'An error occurred')
      setLoading(false)
    }
  }

  const handleCreateTicket = async () => {
    try {
      setCreating(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      
      // Get application to get candidate_id
      const appResponse = await apiClient.get(`/applications/job/${jobId}`)
      const app = (appResponse.data as any[])?.find((a: any) => a.id === applicationId)
      
      if (!app) {
        setError('Application not found')
        return
      }

      // Get job to check interview mode
      const jobResponse = await apiClient.get(`/job-descriptions/${jobId}`)
      const job = jobResponse.data as any
      const interviewMode = job?.interview_mode || 'text'
      setJobInterviewMode(interviewMode)

      const response = await apiClient.post<{ ticket_code: string; id: string }>(`/tickets?expires_in_hours=${expiresInHours}&send_email=true`, {
        candidate_id: app.candidate_id,
        job_description_id: jobId
        // interview_mode not needed - inherits from job
      })
      
      if (response.success && response.data) {
        // Backend returns ticket_code; older field name 'code' is no longer used
        setTicketCode(response.data.ticket_code)
        setTicketId(response.data.id)
        // Check if email was sent automatically
        if (response.message?.includes('email sent')) {
          setEmailSent(true)
        }
      } else {
        setError(response.message || 'Failed to create ticket')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setCreating(false)
    }
  }

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

  const handleCopyCode = async () => {
    const success = await copyToClipboard(ticketCode)
    if (success) {
      setCopiedCode(true)
      setTimeout(() => setCopiedCode(false), 2000)
    }
  }

  const handleCopyLink = async (isVoice: boolean = false) => {
    const link = getInterviewLink(jobId)
    const success = await copyToClipboard(link)
    if (success) {
      if (isVoice) {
        setCopiedVoiceLink(true)
        setTimeout(() => setCopiedVoiceLink(false), 2000)
      } else {
        setCopiedLink(true)
        setTimeout(() => setCopiedLink(false), 2000)
      }
    }
  }

  const handleSendEmail = async () => {
    if (!ticketId) {
      alert('Ticket ID not found')
      return
    }

    try {
      setSendingEmail(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.post(`/emails/send-ticket/${ticketId}`)
      
      if (response.success) {
        setEmailSent(true)
        alert('Ticket email sent successfully!')
      } else {
        alert('Failed to send email: ' + response.message)
      }
    } catch (err: any) {
      console.error('Error sending email:', err)
      alert('Error sending email: ' + (err.message || 'Unknown error'))
    } finally {
      setSendingEmail(false)
    }
  }

  if (ticketCode) {
    const interviewLink = getInterviewLink(jobId)
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h1 className="text-2xl font-bold text-gray-900">Interview Ticket Created</h1>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <div className="py-8 space-y-6">
              {/* Ticket Code */}
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-3">Interview Ticket Code</p>
                <div className="flex items-center justify-center gap-2 mb-4">
                  <div className="bg-primary-100 rounded-lg px-6 py-4 inline-block">
                    <p className="text-3xl font-bold text-primary-700 font-mono">{ticketCode}</p>
                  </div>
                  <button
                    onClick={handleCopyCode}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Copy ticket code"
                  >
                    {copiedCode ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : (
                      <Copy className="w-5 h-5 text-gray-600" />
                    )}
                  </button>
                </div>
                {/* Interview Mode Badge */}
                {jobInterviewMode && (
                  <div className="mt-4 flex items-center justify-center gap-2">
                    <span className="text-sm text-gray-600">Interview Mode (inherited from job):</span>
                    {jobInterviewMode === 'voice' ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700">
                        <Mic className="w-4 h-4" />
                        Voice Interview
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">
                        <Type className="w-4 h-4" />
                        Text Interview
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Interview Links */}
              <div className="border-t pt-6">
                <p className="text-sm text-gray-600 mb-3 text-center font-medium">Interview Links</p>
                <p className="text-xs text-gray-500 text-center mb-4">
                  Share the appropriate link with the candidate. They will use the same ticket code regardless of which link they use.
                </p>
                
                {/* Text Interview Link */}
                <div className="mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Type className="w-4 h-4 text-gray-600" />
                    <span className="text-xs font-medium text-gray-700">Text Interview Link</span>
                  </div>
                  <div className="flex items-center gap-2 bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <LinkIcon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                    <p className="text-sm text-gray-700 flex-1 truncate font-mono">{interviewLink}</p>
                    <button
                      onClick={() => handleCopyLink(false)}
                      className="p-1.5 hover:bg-gray-200 rounded transition-colors flex-shrink-0"
                      title="Copy text interview link"
                    >
                      {copiedLink ? (
                        <Check className="w-4 h-4 text-green-600" />
                      ) : (
                        <Copy className="w-4 h-4 text-gray-600" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Voice Interview Link */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Mic className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-medium text-gray-700">Voice Interview Link</span>
                  </div>
                  <div className="flex items-center gap-2 bg-blue-50 rounded-lg p-3 border border-blue-200">
                    <LinkIcon className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    <p className="text-sm text-blue-700 flex-1 truncate font-mono">{interviewLink}</p>
                    <button
                      onClick={() => handleCopyLink(true)}
                      className="p-1.5 hover:bg-blue-100 rounded transition-colors flex-shrink-0"
                      title="Copy voice interview link"
                    >
                      {copiedVoiceLink ? (
                        <Check className="w-4 h-4 text-green-600" />
                      ) : (
                        <Copy className="w-4 h-4 text-blue-600" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Send Email Section */}
              <div className="border-t pt-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <Mail className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div className="flex-1">
                      <h3 className="font-semibold text-blue-900 mb-1">Send Ticket Email</h3>
                      <p className="text-sm text-blue-700">
                        Automatically send the interview ticket to the candidate via email with your company branding.
                      </p>
                    </div>
                  </div>
                </div>
                <Button
                  variant="primary"
                  onClick={handleSendEmail}
                  loading={sendingEmail}
                  disabled={emailSent}
                  className="w-full"
                >
                  {emailSent ? (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Email Sent!
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Send Ticket Email to Candidate
                    </>
                  )}
                </Button>
              </div>

              <div className="flex gap-4 justify-center pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={handleCopyCode}
                  className="flex items-center gap-2"
                >
                  {copiedCode ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Code Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      <span>Copy Code</span>
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleCopyLink(false)}
                  className="flex items-center gap-2"
                >
                  {copiedLink ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Text Link Copied!</span>
                    </>
                  ) : (
                    <>
                      <Type className="w-4 h-4" />
                      <span>Copy Text Link</span>
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleCopyLink(true)}
                  className="flex items-center gap-2"
                >
                  {copiedVoiceLink ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Voice Link Copied!</span>
                    </>
                  ) : (
                    <>
                      <Mic className="w-4 h-4" />
                      <span>Copy Voice Link</span>
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => router.push(`/dashboard/jobs/${jobId}/applications`)}
                >
                  Back to Applications
                </Button>
              </div>
            </div>
          </Card>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Create Interview Ticket</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="space-y-6">
            <div>
              <p className="text-gray-600 mb-4">
                Create an interview ticket for this qualified candidate. They will use the ticket code to access their interview.
              </p>
            </div>

            <Input
              label="Ticket Expiration (hours)"
              type="number"
              value={expiresInHours.toString()}
              onChange={(e) => setExpiresInHours(parseInt(e.target.value) || 48)}
              min={1}
              max={168}
              helperText="How long the ticket will be valid (default: 48 hours)"
            />


            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={() => router.push(`/dashboard/jobs/${jobId}/applications`)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleCreateTicket}
                loading={creating}
                className="flex-1"
              >
                Create Ticket
              </Button>
            </div>
          </div>
        </Card>
      </main>
    </div>
  )
}

