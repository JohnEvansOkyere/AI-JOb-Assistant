/**
 * Email History Page
 * View all sent emails
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ArrowLeft, Mail, CheckCircle, XCircle, Clock } from 'lucide-react'

export default function EmailHistoryPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [emails, setEmails] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState<any>(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadEmails()
    }
  }, [isAuthenticated, authLoading, router])

  const loadEmails = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<any>('/emails/sent?limit=100')
      if (response.success && response.data) {
        // Handle both response.data (array) and response.data.data (nested)
        const emails = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data?.data) ? response.data.data : [])
        setEmails(emails)
      }
    } catch (err: any) {
      console.error('Error loading emails:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
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
              <h1 className="text-2xl font-bold text-gray-900">Email History</h1>
              <p className="text-gray-600 mt-1">View all sent emails</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Email List */}
          <div className="lg:col-span-1">
            <Card>
              <div className="p-4">
                <h2 className="font-semibold text-gray-900 mb-4">
                  Sent Emails ({emails.length})
                </h2>
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {emails.length === 0 ? (
                    <div className="text-center py-8">
                      <Mail className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No emails sent yet</p>
                    </div>
                  ) : (
                    emails.map((email) => (
                      <button
                        key={email.id}
                        onClick={() => setSelectedEmail(email)}
                        className={`w-full text-left p-3 rounded-lg border transition-colors ${
                          selectedEmail?.id === email.id
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <p className="font-medium text-sm text-gray-900 truncate">
                            {email.subject}
                          </p>
                          {getStatusIcon(email.status)}
                        </div>
                        <p className="text-xs text-gray-600 truncate">
                          {email.recipient_email}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {email.sent_at
                            ? new Date(email.sent_at).toLocaleString()
                            : 'Not sent'}
                        </p>
                      </button>
                    ))
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* Email Details */}
          <div className="lg:col-span-2">
            {selectedEmail ? (
              <Card>
                <div className="p-6">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900 mb-2">
                        {selectedEmail.subject}
                      </h2>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span>To: {selectedEmail.recipient_email}</span>
                        {selectedEmail.recipient_name && (
                          <span>({selectedEmail.recipient_name})</span>
                        )}
                      </div>
                    </div>
                    <span
                      className={`text-xs px-3 py-1 rounded-full ${
                        selectedEmail.status === 'sent'
                          ? 'bg-green-100 text-green-800'
                          : selectedEmail.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {selectedEmail.status}
                    </span>
                  </div>

                  <div className="border-t border-gray-200 pt-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Email Content</h3>
                    <div
                      className="prose max-w-none border border-gray-200 rounded-lg p-6 bg-white"
                      dangerouslySetInnerHTML={{
                        __html: selectedEmail.body_html || '<p>No content</p>',
                      }}
                    />
                  </div>

                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <h3 className="font-semibold text-gray-900 mb-4">Details</h3>
                    <dl className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <dt className="text-gray-600">Sent At</dt>
                        <dd className="text-gray-900">
                          {selectedEmail.sent_at
                            ? new Date(selectedEmail.sent_at).toLocaleString()
                            : 'Not sent'}
                        </dd>
                      </div>
                      {selectedEmail.delivered_at && (
                        <div>
                          <dt className="text-gray-600">Delivered At</dt>
                          <dd className="text-gray-900">
                            {new Date(selectedEmail.delivered_at).toLocaleString()}
                          </dd>
                        </div>
                      )}
                      {selectedEmail.external_email_id && (
                        <div>
                          <dt className="text-gray-600">Email ID</dt>
                          <dd className="text-gray-900 font-mono text-xs">
                            {selectedEmail.external_email_id}
                          </dd>
                        </div>
                      )}
                    </dl>
                  </div>
                </div>
              </Card>
            ) : (
              <Card>
                <div className="p-12 text-center">
                  <Mail className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Select an email to view details</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

