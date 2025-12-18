/**
 * Emails Page
 * Email management - compose, history, and templates
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Mail, Send, History, Settings, Calendar, FileText, Clock } from 'lucide-react'

export default function EmailsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [sentEmails, setSentEmails] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [calendarEvents, setCalendarEvents] = useState<any[]>([])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadSentEmails()
      loadCalendarEvents()
    }
  }, [isAuthenticated, authLoading, router])

  const loadCalendarEvents = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any>('/calendar/events?limit=5')
      if (response.success && response.data) {
        const eventsList = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data?.data) ? response.data.data : [])
        setCalendarEvents(eventsList)
      }
    } catch (err: any) {
      console.error('Error loading calendar events:', err)
    }
  }

  const loadSentEmails = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any>('/emails/sent?limit=10')
      if (response.success && response.data) {
        // Handle both response.data (array) and response.data.data (nested)
        const emails = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data?.data) ? response.data.data : [])
        setSentEmails(emails)
      }
    } catch (err: any) {
      console.error('Error loading emails:', err)
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
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
            <h1 className="text-2xl font-bold text-gray-900">Emails</h1>
            <p className="text-gray-600 mt-1">Manage your email communications</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard/settings/branding')}
            >
              <Settings className="w-4 h-4 mr-2" />
              Branding
            </Button>
            <Button
              variant="primary"
              onClick={() => router.push('/dashboard/emails/compose')}
            >
              <Send className="w-4 h-4 mr-2" />
              Compose Email
            </Button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <Send className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Compose Email</h3>
                  <p className="text-sm text-gray-600">Send a new email</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-4"
                onClick={() => router.push('/dashboard/emails/compose')}
              >
                Compose
              </Button>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <History className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Email History</h3>
                  <p className="text-sm text-gray-600">View sent emails</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-4"
                onClick={() => router.push('/dashboard/emails/history')}
              >
                View History
              </Button>
            </div>
          </Card>

          <Card>
            <div className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Templates</h3>
                  <p className="text-sm text-gray-600">Manage email templates</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-4"
                onClick={() => router.push('/dashboard/emails/templates')}
              >
                Manage Templates
              </Button>
            </div>
          </Card>

          <div 
            className="cursor-pointer"
            onClick={() => router.push('/dashboard/calendar')}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <div className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Calendar</h3>
                  <p className="text-sm text-gray-600">View upcoming events</p>
                </div>
              </div>
              <div className="mt-4 space-y-2">
                {calendarEvents.length > 0 ? (
                  <>
                    {calendarEvents.slice(0, 3).map((event) => (
                      <div key={event.id} className="flex items-center gap-2 text-xs text-gray-600">
                        <Clock className="w-3 h-3" />
                        <span className="truncate">{event.title || 'Untitled Event'}</span>
                      </div>
                    ))}
                    {calendarEvents.length > 3 && (
                      <p className="text-xs text-gray-500">+{calendarEvents.length - 3} more</p>
                    )}
                  </>
                ) : (
                  <p className="text-xs text-gray-500">No upcoming events</p>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-4"
                onClick={(e) => {
                  e.stopPropagation()
                  router.push('/dashboard/calendar')
                }}
              >
                View Calendar
              </Button>
            </div>
            </Card>
          </div>
        </div>

        {/* Recent Emails */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Recent Emails</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/dashboard/emails/history')}
              >
                View All
              </Button>
            </div>

            {sentEmails.length === 0 ? (
              <div className="text-center py-12">
                <Mail className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No emails sent yet</p>
                <Button
                  variant="primary"
                  onClick={() => router.push('/dashboard/emails/compose')}
                >
                  Send Your First Email
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {sentEmails.map((email) => (
                  <div
                    key={email.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-medium text-gray-900">{email.subject}</h3>
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              email.status === 'sent'
                                ? 'bg-green-100 text-green-800'
                                : email.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {email.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          To: {email.recipient_email}
                          {email.recipient_name && ` (${email.recipient_name})`}
                        </p>
                        <p className="text-xs text-gray-500">
                          {email.sent_at
                            ? new Date(email.sent_at).toLocaleString()
                            : 'Not sent yet'}
                        </p>
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

