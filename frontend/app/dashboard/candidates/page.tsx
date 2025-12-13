/**
 * Candidates Page
 * View and manage candidates
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiClient } from '@/lib/api/client'
import { Input } from '@/components/ui/Input'
import { User, Mail, Phone, Briefcase, Calendar, CheckCircle, Clock, XCircle } from 'lucide-react'

interface Candidate {
  id: string
  full_name: string
  email: string
  phone?: string
  created_at: string
  total_applications: number
  latest_application?: {
    id: string
    job_title: string
    status: string
    applied_at: string
    screening_result?: {
      match_score: number
      recommendation: string
    }
  }
  applications: Array<{
    id: string
    job_title: string
    status: string
    applied_at: string
    screening_result?: {
      match_score: number
      recommendation: string
    }
  }>
}

export default function CandidatesPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      loadCandidates()
    }
  }, [isAuthenticated, authLoading, router])

  const loadCandidates = async () => {
    try {
      setLoading(true)
      setError('')
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }
      const response = await apiClient.get<Candidate[]>('/candidates')
      if (response.success && response.data) {
        setCandidates(response.data)
      } else {
        setError(response.message || 'Failed to load candidates')
      }
    } catch (err: any) {
      console.error('Error loading candidates:', err)
      setError(err.message || 'An error occurred while loading candidates')
    } finally {
      setLoading(false)
    }
  }

  const filteredCandidates = candidates.filter(candidate =>
    candidate.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    candidate.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    candidate.latest_application?.job_title?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800', icon: Clock },
      qualified: { label: 'Qualified', className: 'bg-green-100 text-green-800', icon: CheckCircle },
      screening: { label: 'Screening', className: 'bg-blue-100 text-blue-800', icon: Clock },
      rejected: { label: 'Rejected', className: 'bg-red-100 text-red-800', icon: XCircle },
      interview_scheduled: { label: 'Interview Scheduled', className: 'bg-purple-100 text-purple-800', icon: Calendar },
    }
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
    const Icon = config.icon
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${config.className}`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </span>
    )
  }

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading candidates...</p>
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
            <h1 className="text-2xl font-bold text-gray-900">Candidates</h1>
            <p className="text-gray-600 mt-1">View and manage all candidates</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadCandidates} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
            <Button variant="primary" onClick={() => router.push('/dashboard/jobs')}>
              View Jobs
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Search */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <Input
            type="text"
            placeholder="Search by name, email, or job title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {filteredCandidates.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <User className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">
                {searchTerm ? 'No candidates match your search.' : 'No candidates yet.'}
              </p>
              {!searchTerm && (
                <Button variant="primary" onClick={() => router.push('/dashboard/jobs')}>
                  View Job Postings
                </Button>
              )}
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCandidates.map((candidate) => (
              <Card key={candidate.id}>
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        <User className="h-5 w-5 text-gray-400" />
                        {candidate.full_name || 'Unknown'}
                      </h3>
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Mail className="h-4 w-4" />
                          {candidate.email}
                        </div>
                        {candidate.phone && (
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Phone className="h-4 w-4" />
                            {candidate.phone}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {candidate.latest_application && (
                    <div className="border-t pt-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Briefcase className="h-4 w-4" />
                          <span className="font-medium">Latest Application</span>
                        </div>
                        {getStatusBadge(candidate.latest_application.status)}
                      </div>
                      <p className="text-sm font-medium text-gray-900">
                        {candidate.latest_application.job_title}
                      </p>
                      {candidate.latest_application.screening_result && (
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-gray-600">Match Score:</span>
                          <span className={`font-semibold ${
                            candidate.latest_application.screening_result.match_score >= 70
                              ? 'text-green-600'
                              : candidate.latest_application.screening_result.match_score >= 50
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          }`}>
                            {candidate.latest_application.screening_result.match_score}%
                          </span>
                        </div>
                      )}
                      <p className="text-xs text-gray-500">
                        Applied {new Date(candidate.latest_application.applied_at).toLocaleDateString()}
                      </p>
                    </div>
                  )}

                  <div className="border-t pt-4 flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {candidate.total_applications} application{candidate.total_applications !== 1 ? 's' : ''}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/dashboard/candidates/${candidate.id}`)}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
