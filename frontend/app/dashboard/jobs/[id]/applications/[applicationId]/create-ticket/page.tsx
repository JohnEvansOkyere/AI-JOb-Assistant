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
  const [error, setError] = useState('')
  const [ticketCode, setTicketCode] = useState('')
  const [expiresInHours, setExpiresInHours] = useState(48)

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

      const response = await apiClient.post(`/tickets?expires_in_hours=${expiresInHours}`, {
        candidate_id: app.candidate_id,
        job_description_id: jobId
      })
      
      if (response.success && response.data) {
        setTicketCode(response.data.ticket_code)
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

  if (ticketCode) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h1 className="text-2xl font-bold text-gray-900">Interview Ticket Created</h1>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <div className="text-center py-8">
              <div className="mb-6">
                <div className="inline-block bg-primary-100 rounded-lg p-6 mb-4">
                  <p className="text-sm text-gray-600 mb-2">Interview Ticket Code</p>
                  <p className="text-3xl font-bold text-primary-700 font-mono">{ticketCode}</p>
                </div>
              </div>
              
              <p className="text-gray-600 mb-6">
                Share this ticket code with the candidate. They can use it to start their interview.
              </p>
              
              <div className="flex gap-4 justify-center">
                <Button
                  variant="outline"
                  onClick={() => navigator.clipboard.writeText(ticketCode)}
                >
                  Copy Code
                </Button>
                <Button
                  variant="primary"
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

