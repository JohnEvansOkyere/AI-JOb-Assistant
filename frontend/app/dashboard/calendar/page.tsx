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
import { Calendar, Plus, Clock, MapPin, Video } from 'lucide-react'

export default function CalendarPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadEvents()
    }
  }, [isAuthenticated, authLoading, router])

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
            <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
            <p className="text-gray-600 mt-1">Manage interview bookings and events</p>
          </div>
          <Button
            variant="primary"
            onClick={() => {
              // TODO: Open create event modal
              alert('Create event feature coming soon!')
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Event
          </Button>
        </div>

        <Card>
          <div className="p-6">
            {events.length === 0 ? (
              <div className="text-center py-12">
                <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No calendar events yet</p>
                <Button
                  variant="primary"
                  onClick={() => {
                    alert('Create event feature coming soon!')
                  }}
                >
                  Create Your First Event
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="border border-gray-200 rounded-lg p-6 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {event.title}
                          </h3>
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              event.status === 'scheduled'
                                ? 'bg-blue-100 text-blue-800'
                                : event.status === 'confirmed'
                                ? 'bg-green-100 text-green-800'
                                : event.status === 'cancelled'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {event.status}
                          </span>
                        </div>
                        {event.description && (
                          <p className="text-gray-600 mb-4">{event.description}</p>
                        )}
                        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            <span>
                              {new Date(event.start_time).toLocaleString()} -{' '}
                              {new Date(event.end_time).toLocaleTimeString()}
                            </span>
                          </div>
                          {event.location && (
                            <div className="flex items-center gap-2">
                              {event.is_virtual ? (
                                <Video className="w-4 h-4" />
                              ) : (
                                <MapPin className="w-4 h-4" />
                              )}
                              <span>{event.location}</span>
                            </div>
                          )}
                          {event.video_link && (
                            <a
                              href={event.video_link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary-600 hover:text-primary-700"
                            >
                              Join Meeting
                            </a>
                          )}
                        </div>
                        {event.attendee_emails && event.attendee_emails.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <p className="text-sm font-medium text-gray-700 mb-2">Attendees:</p>
                            <div className="flex flex-wrap gap-2">
                              {event.attendee_emails.map((email: string, idx: number) => (
                                <span
                                  key={idx}
                                  className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                                >
                                  {email}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}

