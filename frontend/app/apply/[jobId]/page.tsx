/**
 * Public Job Application Page
 * LinkedIn-style application form (no auth required)
 */

'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'
import { JobDescription } from '@/types'

interface PublicFormField {
  field_key: string
  field_label: string
  field_type: string
  field_options?: { options?: string[] }
  is_required: boolean
  placeholder?: string
  help_text?: string
}

export default function ApplyPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string
  
  const [job, setJob] = useState<JobDescription | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    phone: '',
    cover_letter: '',
  })
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [customFields, setCustomFields] = useState<PublicFormField[]>([])
  const [customFieldValues, setCustomFieldValues] = useState<Record<string, any>>({})

  useEffect(() => {
    loadJob()
  }, [jobId])

  const loadJob = async () => {
    try {
      // Public endpoint to get job details
      const jobResponse = await apiClient.get<JobDescription>(`/public/job-descriptions/${jobId}`)
      if (jobResponse.success && jobResponse.data) {
        setJob(jobResponse.data)
      } else {
        setError('Job not found')
        setLoading(false)
        return
      }

      // Load custom form fields
      try {
        const fieldsResponse = await apiClient.get<PublicFormField[]>(`/application-forms/fields/job/${jobId}/public`)
        if (fieldsResponse.success && fieldsResponse.data) {
          // Explicitly cast because apiClient's generic type is not inferred correctly in some builds
          setCustomFields(fieldsResponse.data as PublicFormField[])
          // Initialize custom field values
          const initialValues: Record<string, any> = {}
          fieldsResponse.data.forEach((field: any) => {
            // Initialize based on field type
            if (field.field_type === 'checkbox') {
              initialValues[field.field_key] = []
            } else {
              initialValues[field.field_key] = ''
            }
          })
          setCustomFieldValues(initialValues)
        }
      } catch (err) {
        // Custom fields are optional, don't fail if they don't exist
        console.log('No custom fields found')
      }
    } catch (err: any) {
      setError('Failed to load job details')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    if (!cvFile) {
      setError('Please upload your CV')
      setSubmitting(false)
      return
    }

    try {
      const formDataToSend = new FormData()
      formDataToSend.append('job_description_id', jobId)
      formDataToSend.append('email', formData.email)
      formDataToSend.append('full_name', formData.full_name)
      if (formData.phone) {
        formDataToSend.append('phone', formData.phone)
      }
      if (formData.cover_letter) {
        formDataToSend.append('cover_letter', formData.cover_letter)
      }
      formDataToSend.append('cv_file', cvFile)

      // Add custom fields as JSON
      if (Object.keys(customFieldValues).length > 0) {
        formDataToSend.append('custom_fields', JSON.stringify(customFieldValues))
      }

      const response = await apiClient.upload('/applications/apply', formDataToSend)
      
      if (response.success) {
        setSuccess(true)
        // Reset form
        setFormData({ email: '', full_name: '', phone: '', cover_letter: '' })
        setCvFile(null)
      } else {
        setError(response.message || 'Failed to submit application')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred while submitting your application')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card>
          <div className="text-center py-12">
            <p className="text-red-600 mb-4">{error || 'Job not found'}</p>
            <Button variant="outline" onClick={() => router.push('/')}>
              Go Home
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card>
          <div className="text-center py-12">
            <div className="mb-4">
              <svg className="mx-auto h-16 w-16 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h2>
            <p className="text-gray-600 mb-6">
              Thank you for your interest. We've received your application and will review it shortly.
            </p>
            <Button variant="primary" onClick={() => router.push('/')}>
              Done
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Job Preview - Full Details */}
        <Card className="mb-6">
          <div className="space-y-6">
            {/* Job Title and Location */}
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-3">{job.title}</h1>
              {job.location && (
                <div className="flex items-center gap-2 text-gray-600">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span className="text-lg">{job.location}</span>
                </div>
              )}
            </div>

            {/* Job Description */}
            {job.description && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">About the Opportunity</h2>
                <div className="prose max-w-none">
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{job.description}</p>
                </div>
              </div>
            )}

            {/* Requirements */}
            {job.requirements && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">Requirements</h2>
                <div className="prose max-w-none">
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{job.requirements}</p>
                </div>
              </div>
            )}

            {/* Experience Level */}
            {job.experience_level && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">Experience Level</h2>
                <p className="text-gray-700 capitalize">{job.experience_level}</p>
              </div>
            )}


            {/* Employment Type */}
            {job.employment_type && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">Employment Type</h2>
                <p className="text-gray-700 capitalize">{job.employment_type}</p>
              </div>
            )}

          </div>
        </Card>

        {/* Application Form */}
        <Card title="Apply for this Position">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-700">Personal Information</h3>
              
              <Input
                label="Full Name *"
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
                placeholder="John Doe"
              />

              <Input
                label="Email *"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                placeholder="you@example.com"
              />

              <Input
                label="Phone Number"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+1 (555) 123-4567"
              />
            </div>

            <div className="border-t pt-4 space-y-4">
              <h3 className="text-sm font-semibold text-gray-700">Required Documents</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CV/Resume * (PDF, DOCX, or TXT)
                </label>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {cvFile && (
                  <p className="mt-1 text-sm text-gray-500">Selected: {cvFile.name}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">Upload your CV or resume in PDF, DOCX, or TXT format</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cover Letter
                </label>
                <textarea
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={6}
                  value={formData.cover_letter}
                  onChange={(e) => setFormData({ ...formData, cover_letter: e.target.value })}
                  placeholder="Tell us why you're interested in this position..."
                />
                <p className="mt-1 text-xs text-gray-500">Optional: Share why you're interested in this role</p>
              </div>
            </div>

            {/* Custom Form Fields */}
            {customFields.length > 0 && (
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Information</h3>
                <div className="space-y-4">
                  {customFields.map((field) => (
                    <div key={field.field_key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {field.field_label} {field.is_required && <span className="text-red-500">*</span>}
                      </label>
                      {field.field_type === 'textarea' ? (
                        <textarea
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          rows={4}
                          value={customFieldValues[field.field_key] || ''}
                          onChange={(e) => setCustomFieldValues({ ...customFieldValues, [field.field_key]: e.target.value })}
                          placeholder={field.placeholder}
                          required={field.is_required}
                        />
                      ) : field.field_type === 'select' ? (
                        <select
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          value={customFieldValues[field.field_key] || ''}
                          onChange={(e) => setCustomFieldValues({ ...customFieldValues, [field.field_key]: e.target.value })}
                          required={field.is_required}
                        >
                          <option value="">Select...</option>
                          {field.field_options?.options?.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      ) : field.field_type === 'radio' ? (
                        <div className="space-y-2">
                          {field.field_options?.options?.map((opt) => (
                            <label key={opt} className="flex items-center">
                              <input
                                type="radio"
                                name={field.field_key}
                                value={opt}
                                checked={customFieldValues[field.field_key] === opt}
                                onChange={(e) => setCustomFieldValues({ ...customFieldValues, [field.field_key]: e.target.value })}
                                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                                required={field.is_required}
                              />
                              <span className="ml-2 text-sm text-gray-700">{opt}</span>
                            </label>
                          ))}
                        </div>
                      ) : field.field_type === 'checkbox' ? (
                        <div className="space-y-2">
                          {field.field_options?.options?.map((opt) => (
                            <label key={opt} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={(customFieldValues[field.field_key] || []).includes(opt)}
                                onChange={(e) => {
                                  const current = customFieldValues[field.field_key] || []
                                  const updated = e.target.checked
                                    ? [...current, opt]
                                    : current.filter((v: string) => v !== opt)
                                  setCustomFieldValues({ ...customFieldValues, [field.field_key]: updated })
                                }}
                                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                              />
                              <span className="ml-2 text-sm text-gray-700">{opt}</span>
                            </label>
                          ))}
                        </div>
                      ) : (
                        <Input
                          type={field.field_type === 'number' ? 'number' : field.field_type === 'date' ? 'date' : 'text'}
                          value={customFieldValues[field.field_key] || ''}
                          onChange={(e) => setCustomFieldValues({ ...customFieldValues, [field.field_key]: e.target.value })}
                          placeholder={field.placeholder}
                          required={field.is_required}
                        />
                      )}
                      {field.help_text && (
                        <p className="mt-1 text-xs text-gray-500">{field.help_text}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={submitting}
              className="w-full"
            >
              Submit Application
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}

