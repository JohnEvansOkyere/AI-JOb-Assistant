/**
 * Compose Email Page
 * Focused on Interview Invitations and Offer Letters
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { ArrowLeft, Send, Eye, FileText, Mail, CheckCircle, X } from 'lucide-react'

type EmailType = 'interview' | 'offer'

export default function ComposeEmailPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [emailType, setEmailType] = useState<EmailType>('interview')
  const [loading, setLoading] = useState(false)
  const [loadingCandidates, setLoadingCandidates] = useState(false)
  const [candidates, setCandidates] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [showPreview, setShowPreview] = useState(false)
  const [previewHtml, setPreviewHtml] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewData, setPreviewData] = useState<{
    subject: string
    recipient_email: string
    recipient_name: string
  } | null>(null)
  const [interviewPreviewHtml, setInterviewPreviewHtml] = useState<string>('')
  const [interviewPreviewLoading, setInterviewPreviewLoading] = useState(false)
  const [interviewPreviewData, setInterviewPreviewData] = useState<{
    subject: string
    recipient_email: string
    recipient_name: string
  } | null>(null)
  
  // Sender information (shared between both forms)
  const [senderInfo, setSenderInfo] = useState({
    from_email: '', // e.g., john.doe@gmail.com or hr@company.com
    from_name: '',  // e.g., "John Doe - HR Manager"
    email_provider: 'resend', // 'resend' or 'smtp'
  })
  
  // Interview invitation form
  const [interviewForm, setInterviewForm] = useState({
    candidate_id: '',
    job_description_id: '',
    ticket_id: '', // Optional - if ticket already exists
  })
  
  // Offer letter form
  const [offerForm, setOfferForm] = useState({
    candidate_id: '',
    job_description_id: '',
    offer_letter_file: null as File | null,
    salary: '',
    start_date: '',
    location: '',
    employment_type: '',
  })

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadCandidates()
      loadJobs()
      
      // Check if coming from ticket creation
      const ticketId = searchParams.get('ticket_id')
      const candidateId = searchParams.get('candidate_id')
      const jobId = searchParams.get('job_id')
      
      if (ticketId && candidateId && jobId) {
        setEmailType('interview')
        setInterviewForm({
          candidate_id: candidateId,
          job_description_id: jobId,
          ticket_id: ticketId,
        })
      }
    }
  }, [isAuthenticated, authLoading, router, searchParams])

  const loadCandidates = async () => {
    try {
      setLoadingCandidates(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any>('/candidates')
      if (response.success && response.data) {
        const candidatesList = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data?.data) ? response.data.data : [])
        setCandidates(candidatesList)
      }
    } catch (err: any) {
      console.error('Error loading candidates:', err)
    } finally {
      setLoadingCandidates(false)
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

  const handleSendInterviewInvitation = async () => {
    if (!interviewForm.candidate_id || !interviewForm.job_description_id) {
      alert('Please select a candidate and job')
      return
    }

    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      if (interviewForm.ticket_id) {
        // Send email for existing ticket
        const formData = new FormData()
        if (senderInfo.from_email) formData.append('from_email', senderInfo.from_email)
        if (senderInfo.from_name) formData.append('from_name', senderInfo.from_name)
        if (senderInfo.email_provider) formData.append('email_provider', senderInfo.email_provider)
        
        const response = await apiClient.upload(`/emails/send-ticket/${interviewForm.ticket_id}`, formData)
        if (response.success) {
          alert('Interview invitation email sent successfully!')
          router.push('/dashboard/emails/history')
        } else {
          alert('Failed to send email: ' + response.message)
        }
      } else {
        // Create ticket and send email automatically using send-interview-invitation endpoint
        const response = await apiClient.post('/emails/send-interview-invitation', {
          candidate_id: interviewForm.candidate_id,
          job_description_id: interviewForm.job_description_id,
          expires_in_hours: 48,
          from_email: senderInfo.from_email || undefined,
          from_name: senderInfo.from_name || undefined,
          email_provider: senderInfo.email_provider || undefined,
        })
        if (response.success) {
          alert('Ticket created and interview invitation email sent successfully!')
          router.push('/dashboard/emails/history')
        } else {
          alert('Failed to create ticket: ' + response.message)
        }
      }
    } catch (err: any) {
      console.error('Error sending interview invitation:', err)
      alert('Error: ' + (err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  const handlePreviewInterviewInvitation = async () => {
    if (!interviewForm.candidate_id || !interviewForm.job_description_id) {
      alert('Please select a candidate and job to preview')
      return
    }

    try {
      setInterviewPreviewLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.post<any>('/emails/preview-interview-invitation', {
        candidate_id: interviewForm.candidate_id,
        job_description_id: interviewForm.job_description_id,
        expires_in_hours: 48,
        from_email: senderInfo.from_email || undefined,
        from_name: senderInfo.from_name || undefined,
        email_provider: senderInfo.email_provider || undefined,
      })

      if (response.success && response.data) {
        const data = response.data as { html?: string; subject?: string; recipient_email?: string; recipient_name?: string }
        if (data.html) {
          setInterviewPreviewHtml(data.html)
        }
        setInterviewPreviewData({
          subject: data.subject || '',
          recipient_email: data.recipient_email || '',
          recipient_name: data.recipient_name || '',
        })
        setShowPreview(true)
      } else {
        alert('Failed to generate preview: ' + response.message)
      }
    } catch (err: any) {
      console.error('Error generating preview:', err)
      alert('Error: ' + (err.message || 'Unknown error'))
    } finally {
      setInterviewPreviewLoading(false)
    }
  }

  const handlePreviewOfferLetter = async () => {
    if (!offerForm.candidate_id || !offerForm.job_description_id) {
      alert('Please select a candidate and job to preview')
      return
    }

    try {
      setPreviewLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.post<any>('/emails/preview-offer-letter', {
        candidate_id: offerForm.candidate_id,
        job_description_id: offerForm.job_description_id,
        salary: offerForm.salary || null,
        start_date: offerForm.start_date || null,
        location: offerForm.location || null,
        employment_type: offerForm.employment_type || null,
        from_email: senderInfo.from_email || undefined,
        from_name: senderInfo.from_name || undefined,
        email_provider: senderInfo.email_provider || undefined,
      })

      if (response.success && response.data) {
        const data = response.data as { html?: string; subject?: string; recipient_email?: string; recipient_name?: string }
        if (data.html) {
          setPreviewHtml(data.html)
        }
        setPreviewData({
          subject: data.subject || '',
          recipient_email: data.recipient_email || '',
          recipient_name: data.recipient_name || '',
        })
        setShowPreview(true)
      } else {
        alert('Failed to generate preview: ' + response.message)
      }
    } catch (err: any) {
      console.error('Error generating preview:', err)
      alert('Error: ' + (err.message || 'Unknown error'))
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleSendOfferLetter = async () => {
    if (!offerForm.candidate_id || !offerForm.job_description_id || !offerForm.offer_letter_file) {
      alert('Please select candidate, job, and upload offer letter PDF')
      return
    }

    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const formData = new FormData()
      formData.append('candidate_id', offerForm.candidate_id)
      formData.append('job_description_id', offerForm.job_description_id)
      formData.append('offer_letter_file', offerForm.offer_letter_file)
      if (offerForm.salary) formData.append('salary', offerForm.salary)
      if (offerForm.start_date) formData.append('start_date', offerForm.start_date)
      if (offerForm.location) formData.append('location', offerForm.location)
      if (offerForm.employment_type) formData.append('employment_type', offerForm.employment_type)
      if (senderInfo.from_email) formData.append('from_email', senderInfo.from_email)
      if (senderInfo.from_name) formData.append('from_name', senderInfo.from_name)
      if (senderInfo.email_provider) formData.append('email_provider', senderInfo.email_provider)

      const response = await apiClient.upload('/emails/send-offer-letter', formData)

      if (response.success) {
        alert('Offer letter email sent successfully!')
        router.push('/dashboard/emails/history')
      } else {
        alert('Failed to send offer letter: ' + response.message)
      }
    } catch (err: any) {
      console.error('Error sending offer letter:', err)
      alert('Error: ' + (err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  const getSelectedCandidate = () => {
    return candidates.find(c => c.id === interviewForm.candidate_id || c.id === offerForm.candidate_id)
  }

  const getSelectedJob = () => {
    return jobs.find(j => j.id === interviewForm.job_description_id || j.id === offerForm.job_description_id)
  }

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
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
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard/emails')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Compose Email</h1>
              <p className="text-gray-600 mt-1">Send interview invitations or offer letters</p>
            </div>
          </div>
        </div>

        {/* Email Type Selector */}
        <Card>
          <div className="p-4">
            <div className="flex gap-4">
              <button
                onClick={() => setEmailType('interview')}
                className={`flex-1 flex items-center justify-center gap-3 p-4 rounded-lg border-2 transition-colors ${
                  emailType === 'interview'
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Mail className={`w-6 h-6 ${emailType === 'interview' ? 'text-primary-600' : 'text-gray-400'}`} />
                <div className="text-left">
                  <h3 className="font-semibold text-gray-900">Interview Invitation</h3>
                  <p className="text-sm text-gray-600">Send ticket code and interview link</p>
                </div>
              </button>
              <button
                onClick={() => setEmailType('offer')}
                className={`flex-1 flex items-center justify-center gap-3 p-4 rounded-lg border-2 transition-colors ${
                  emailType === 'offer'
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <FileText className={`w-6 h-6 ${emailType === 'offer' ? 'text-primary-600' : 'text-gray-400'}`} />
                <div className="text-left">
                  <h3 className="font-semibold text-gray-900">Offer Letter</h3>
                  <p className="text-sm text-gray-600">Send offer letter with PDF attachment</p>
                </div>
              </button>
            </div>
          </div>
        </Card>

        {/* Interview Invitation Form */}
        {emailType === 'interview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <div className="p-6 space-y-6">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Interview Invitation</h2>
                    <p className="text-gray-600 mb-6">
                      This will automatically create an interview ticket and send an email to the candidate with:
                    </p>
                    <ul className="space-y-2 text-sm text-gray-600 mb-6">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Interview ticket code
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Direct interview link
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Job details and instructions
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Company branding and letterhead
                      </li>
                    </ul>
                  </div>

                  {interviewForm.ticket_id && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-800">
                        <strong>Note:</strong> Using existing ticket. Email will be sent for ticket ID: {interviewForm.ticket_id}
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <div className="p-6 space-y-4">
                  <h3 className="font-semibold text-gray-900">Sender Information</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      From Email
                    </label>
                    <input
                      type="email"
                      value={senderInfo.from_email}
                      onChange={(e) => setSenderInfo({ ...senderInfo, from_email: e.target.value })}
                      placeholder="your.email@gmail.com"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Leave empty to use default from settings
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      From Name
                    </label>
                    <input
                      type="text"
                      value={senderInfo.from_name}
                      onChange={(e) => setSenderInfo({ ...senderInfo, from_name: e.target.value })}
                      placeholder="John Doe - HR Manager"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Leave empty to use default from settings
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Provider
                    </label>
                    <select
                      value={senderInfo.email_provider}
                      onChange={(e) => setSenderInfo({ ...senderInfo, email_provider: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="resend">Resend API (Recommended)</option>
                      <option value="smtp">Gmail SMTP / Other SMTP</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Choose how to send the email
                    </p>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="p-6 space-y-4">
                  <h3 className="font-semibold text-gray-900">Select Candidate & Job</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Candidate *
                    </label>
                    <select
                      value={interviewForm.candidate_id}
                      onChange={(e) => setInterviewForm({ ...interviewForm, candidate_id: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select candidate...</option>
                      {candidates.map((candidate) => (
                        <option key={candidate.id} value={candidate.id}>
                          {candidate.full_name || candidate.email}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Position *
                    </label>
                    <select
                      value={interviewForm.job_description_id}
                      onChange={(e) => setInterviewForm({ ...interviewForm, job_description_id: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select job...</option>
                      {jobs.map((job) => (
                        <option key={job.id} value={job.id}>
                          {job.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  {getSelectedCandidate() && getSelectedJob() && (
                    <div className="bg-gray-50 rounded-lg p-4 mt-4">
                      <p className="text-sm text-gray-600 mb-2">Email will be sent to:</p>
                      <p className="font-medium text-gray-900">{getSelectedCandidate()?.email}</p>
                      <p className="text-sm text-gray-600 mt-2">For position:</p>
                      <p className="font-medium text-gray-900">{getSelectedJob()?.title}</p>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={handlePreviewInterviewInvitation}
                      loading={interviewPreviewLoading}
                      className="flex-1"
                      disabled={!interviewForm.candidate_id || !interviewForm.job_description_id}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Preview
                    </Button>
                    <Button
                      variant="primary"
                      onClick={handleSendInterviewInvitation}
                      loading={loading}
                      className="flex-1"
                      disabled={!interviewForm.candidate_id || !interviewForm.job_description_id}
                    >
                      <Send className="w-4 h-4 mr-2" />
                      {interviewForm.ticket_id ? 'Send Email' : 'Create & Send'}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* Offer Letter Form */}
        {emailType === 'offer' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <div className="p-6 space-y-6">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Offer Letter</h2>
                    <p className="text-gray-600 mb-6">
                      Send a job offer letter to qualified candidates with PDF attachment.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Offer Letter PDF *
                      </label>
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setOfferForm({ ...offerForm, offer_letter_file: e.target.files?.[0] || null })}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                      />
                      <p className="mt-2 text-xs text-gray-500">
                        Upload the offer letter PDF that will be attached to the email
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        label="Salary (Optional)"
                        value={offerForm.salary}
                        onChange={(e) => setOfferForm({ ...offerForm, salary: e.target.value })}
                        placeholder="e.g., $80,000 - $100,000"
                      />
                      <Input
                        label="Start Date (Optional)"
                        type="date"
                        value={offerForm.start_date}
                        onChange={(e) => setOfferForm({ ...offerForm, start_date: e.target.value })}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        label="Location (Optional)"
                        value={offerForm.location}
                        onChange={(e) => setOfferForm({ ...offerForm, location: e.target.value })}
                        placeholder="e.g., New York, NY"
                      />
                      <Input
                        label="Employment Type (Optional)"
                        value={offerForm.employment_type}
                        onChange={(e) => setOfferForm({ ...offerForm, employment_type: e.target.value })}
                        placeholder="e.g., Full-time, Remote"
                      />
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <div className="p-6 space-y-4">
                  <h3 className="font-semibold text-gray-900">Sender Information</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      From Email
                    </label>
                    <input
                      type="email"
                      value={senderInfo.from_email}
                      onChange={(e) => setSenderInfo({ ...senderInfo, from_email: e.target.value })}
                      placeholder="your.email@gmail.com"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Leave empty to use default from settings
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      From Name
                    </label>
                    <input
                      type="text"
                      value={senderInfo.from_name}
                      onChange={(e) => setSenderInfo({ ...senderInfo, from_name: e.target.value })}
                      placeholder="John Doe - HR Manager"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Leave empty to use default from settings
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Provider
                    </label>
                    <select
                      value={senderInfo.email_provider}
                      onChange={(e) => setSenderInfo({ ...senderInfo, email_provider: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="resend">Resend API (Recommended)</option>
                      <option value="smtp">Gmail SMTP / Other SMTP</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Choose how to send the email
                    </p>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="p-6 space-y-4">
                  <h3 className="font-semibold text-gray-900">Select Candidate & Job</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Candidate *
                    </label>
                    <select
                      value={offerForm.candidate_id}
                      onChange={(e) => setOfferForm({ ...offerForm, candidate_id: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select candidate...</option>
                      {candidates.map((candidate) => (
                        <option key={candidate.id} value={candidate.id}>
                          {candidate.full_name || candidate.email}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Position *
                    </label>
                    <select
                      value={offerForm.job_description_id}
                      onChange={(e) => setOfferForm({ ...offerForm, job_description_id: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      required
                    >
                      <option value="">Select job...</option>
                      {jobs.map((job) => (
                        <option key={job.id} value={job.id}>
                          {job.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  {getSelectedCandidate() && getSelectedJob() && (
                    <div className="bg-gray-50 rounded-lg p-4 mt-4">
                      <p className="text-sm text-gray-600 mb-2">Email will be sent to:</p>
                      <p className="font-medium text-gray-900">{getSelectedCandidate()?.email}</p>
                      <p className="text-sm text-gray-600 mt-2">For position:</p>
                      <p className="font-medium text-gray-900">{getSelectedJob()?.title}</p>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={handlePreviewOfferLetter}
                      loading={previewLoading}
                      className="flex-1"
                      disabled={!offerForm.candidate_id || !offerForm.job_description_id}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Preview
                    </Button>
                    <Button
                      variant="primary"
                      onClick={handleSendOfferLetter}
                      loading={loading}
                      className="flex-1"
                      disabled={!offerForm.candidate_id || !offerForm.job_description_id || !offerForm.offer_letter_file}
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Send
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* Preview Modal */}
        {showPreview && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Email Preview</h2>
                  {(previewData || interviewPreviewData) && (
                    <div className="mt-2 text-sm text-gray-600">
                      <p><strong>To:</strong> {(previewData || interviewPreviewData)?.recipient_name} &lt;{(previewData || interviewPreviewData)?.recipient_email}&gt;</p>
                      <p><strong>Subject:</strong> {(previewData || interviewPreviewData)?.subject}</p>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => {
                    setShowPreview(false)
                    setPreviewHtml('')
                    setInterviewPreviewHtml('')
                    setPreviewData(null)
                    setInterviewPreviewData(null)
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded hover:bg-gray-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Body - Email Preview */}
              <div className="flex-1 overflow-auto p-6 bg-gray-50">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-2xl mx-auto">
                  <div
                    dangerouslySetInnerHTML={{ __html: previewHtml || interviewPreviewHtml }}
                    className="email-preview prose prose-sm max-w-none"
                    style={{
                      fontFamily: 'Arial, sans-serif',
                      lineHeight: '1.6',
                      color: '#333',
                    }}
                  />
                  {emailType === 'offer' && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <strong>Note:</strong> This is a preview. The actual email will include the PDF attachment and may look slightly different in email clients.
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowPreview(false)
                    setPreviewHtml('')
                    setInterviewPreviewHtml('')
                    setPreviewData(null)
                    setInterviewPreviewData(null)
                  }}
                >
                  Close
                </Button>
                {emailType === 'offer' && (
                  <Button
                    variant="primary"
                    onClick={() => {
                      setShowPreview(false)
                      if (offerForm.offer_letter_file) {
                        handleSendOfferLetter()
                      } else {
                        alert('Please upload the offer letter PDF before sending')
                      }
                    }}
                    disabled={!offerForm.offer_letter_file}
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Send Email
                  </Button>
                )}
                {emailType === 'interview' && (
                  <Button
                    variant="primary"
                    onClick={() => {
                      setShowPreview(false)
                      handleSendInterviewInvitation()
                    }}
                    disabled={!interviewForm.candidate_id || !interviewForm.job_description_id}
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Send Email
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
