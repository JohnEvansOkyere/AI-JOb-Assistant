/**
 * Calendar Page
 * View and manage calendar events/interview bookings
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Calendar, Plus, Clock, MapPin, Video, X } from 'lucide-react'
import { CalendarView } from '@/components/ui/CalendarView'

export default function CalendarPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [candidates, setCandidates] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [loadingData, setLoadingData] = useState(false)
  
  const [formData, setFormData] = useState({
    candidate_id: '',
    job_description_id: '',
    title: '',
    start_time: '',
    end_time: '',
    description: '',
    location: '',
    is_virtual: false,
    video_link: '',
    attendee_emails: '',
    attendee_names: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  })

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadEvents()
      loadCandidates()
      loadJobs()
    }
  }, [isAuthenticated, authLoading, router])
  
  const loadCandidates = async () => {
    try {
      setLoadingData(true)
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
      setLoadingData(false)
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

  const loadEvents = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any>('/calendar/events')
      if (response.success && response.data) {
        // Handle both response.data (array) and response.data.data (nested)
        const eventsList = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data?.data) ? response.data.data : [])
        setEvents(eventsList)
      }
    } catch (err: any) {
      console.error('Error loading events:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateEvent = async () => {
    if (!formData.candidate_id || !formData.title || !formData.start_time || !formData.end_time) {
      alert('Please fill in all required fields (Candidate, Title, Start Time, End Time)')
      return
    }

    try {
      setSubmitting(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      // Parse attendee emails and names
      const attendee_emails = formData.attendee_emails
        .split(',')
        .map(email => email.trim())
        .filter(email => email.length > 0)
      const attendee_names = formData.attendee_names
        .split(',')
        .map(name => name.trim())
        .filter(name => name.length > 0)

      const payload: any = {
        candidate_id: formData.candidate_id,
        title: formData.title,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        timezone: formData.timezone,
      }

      if (formData.job_description_id) {
        payload.job_description_id = formData.job_description_id
      }
      if (formData.description) {
        payload.description = formData.description
      }
      if (formData.location) {
        payload.location = formData.location
      }
      if (formData.is_virtual) {
        payload.is_virtual = true
        if (formData.video_link) {
          payload.video_link = formData.video_link
        }
      }
      if (attendee_emails.length > 0) {
        payload.attendee_emails = attendee_emails
      }
      if (attendee_names.length > 0) {
        payload.attendee_names = attendee_names
      }

      const response = await apiClient.post('/calendar/events', payload)

      if (response.success) {
        alert('Calendar event created successfully!')
        setShowCreateModal(false)
        // Reset form
        setFormData({
          candidate_id: '',
          job_description_id: '',
          title: '',
          start_time: '',
          end_time: '',
          description: '',
          location: '',
          is_virtual: false,
          video_link: '',
          attendee_emails: '',
          attendee_names: '',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
        })
        // Reload events
        loadEvents()
      } else {
        alert('Failed to create event: ' + response.message)
      }
    } catch (err: any) {
      console.error('Error creating event:', err)
      alert('Error: ' + (err.message || 'Unknown error'))
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading || loading) {
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
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Calendar</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Manage interview bookings and events</p>
          </div>
          <Button
            variant="primary"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Event
          </Button>
        </div>

        {/* Enhanced Calendar View */}
        <CalendarView
          events={events}
          onEventClick={(event) => {
            // Could open event details modal here
            console.log('Event clicked:', event)
          }}
          onDateClick={(date) => {
            // Could pre-fill create modal with selected date
            setFormData(prev => ({
              ...prev,
              start_time: date.toISOString().slice(0, 16),
              end_time: new Date(date.getTime() + 60 * 60 * 1000).toISOString().slice(0, 16),
            }))
            setShowCreateModal(true)
          }}
        />
      </div>

      {/* Create Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Create Calendar Event</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Candidate * <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.candidate_id}
                    onChange={(e) => setFormData({ ...formData, candidate_id: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Job Position (Optional)
                  </label>
                  <select
                    value={formData.job_description_id}
                    onChange={(e) => setFormData({ ...formData, job_description_id: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Select job...</option>
                    {jobs.map((job) => (
                      <option key={job.id} value={job.id}>
                        {job.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Event Title * <span className="text-red-500">*</span>
                </label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g., Interview with John Doe"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Start Time * <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    End Time * <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                  placeholder="Event description or notes..."
                />
              </div>

              <div>
                <label className="flex items-center gap-2 mb-4">
                  <input
                    type="checkbox"
                    checked={formData.is_virtual}
                    onChange={(e) => setFormData({ ...formData, is_virtual: e.target.checked })}
                    className="w-4 h-4 text-primary-600 border-gray-300 dark:border-gray-600 rounded focus:ring-primary-500 bg-white dark:bg-gray-700"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Virtual Event</span>
                </label>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {formData.is_virtual ? 'Video Link (Zoom, Google Meet, etc.)' : 'Location'}
                  </label>
                  <Input
                    value={formData.is_virtual ? formData.video_link : formData.location}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      [formData.is_virtual ? 'video_link' : 'location']: e.target.value 
                    })}
                    placeholder={formData.is_virtual ? 'https://zoom.us/j/...' : 'Office address or meeting room'}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Timezone
                  </label>
                  <input
                    type="text"
                    value={formData.timezone}
                    onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white"
                    readOnly
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Auto-detected from your browser</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Attendee Emails (comma-separated)
                  </label>
                  <Input
                    value={formData.attendee_emails}
                    onChange={(e) => setFormData({ ...formData, attendee_emails: e.target.value })}
                    placeholder="email1@example.com, email2@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Attendee Names (comma-separated)
                  </label>
                  <Input
                    value={formData.attendee_names}
                    onChange={(e) => setFormData({ ...formData, attendee_names: e.target.value })}
                    placeholder="John Doe, Jane Smith"
                  />
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 sticky bottom-0">
              <Button
                variant="outline"
                onClick={() => setShowCreateModal(false)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleCreateEvent}
                loading={submitting}
              >
                Create Event
              </Button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}

