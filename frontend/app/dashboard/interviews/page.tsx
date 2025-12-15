/**
 * Interviews Page
 * View and manage interview sessions
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiClient } from '@/lib/api/client'

interface InterviewRow {
  id: string
  status: string
  created_at: string
  job_description_id: string
  job_title?: string | null
  candidate?: {
    id: string
    full_name?: string | null
    email?: string | null
  } | null
  report?: {
    skill_match_score?: number | null
    hiring_recommendation?: string | null
    strengths?: string[] | null
    weaknesses?: string[] | null
    red_flags?: string[] | null
    experience_level?: string | null
    recommendation_justification?: string | null
    recruiter_notes?: string | null
    created_at?: string
  } | null
}

export default function InterviewsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [interviews, setInterviews] = useState<InterviewRow[]>([])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }
    if (!authLoading && isAuthenticated) {
      loadInterviews()
    }
  }, [isAuthenticated, authLoading, router])

  const loadInterviews = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.get<InterviewRow[]>('/interviews')
      if (response.success && Array.isArray(response.data)) {
        setInterviews(response.data)
      } else {
        setError(response.message || 'Failed to load interviews')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load interviews')
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
            <p className="mt-4 text-gray-600">Loading interviews...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const hasData = interviews.length > 0

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Interviews</h1>
          <p className="text-gray-600 mt-1">Monitor interview sessions and AI insights.</p>
        </div>

        {error && (
          <Card>
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </Card>
        )}

        <Card>
          {!hasData ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-2">No interviews yet.</p>
              <p className="text-sm text-gray-500 mb-4">
                Once candidates complete AI interviews, you&apos;ll see their sessions and AI summaries
                here.
              </p>
              <Button variant="outline" onClick={() => router.push('/dashboard')}>
                Back to Dashboard
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs font-semibold text-gray-500 uppercase">
                    <th className="py-3 pr-4">Candidate</th>
                    <th className="py-3 pr-4">Job</th>
                    <th className="py-3 pr-4">Status</th>
                    <th className="py-3 pr-4">Skill Match</th>
                    <th className="py-3 pr-4">Recommendation</th>
                    <th className="py-3 pr-4">Key Strengths</th>
                    <th className="py-3 pr-4">Key Weaknesses</th>
                    <th className="py-3 pr-4">Red Flags</th>
                    <th className="py-3 pr-4">Experience</th>
                    <th className="py-3 pr-4">Report Summary</th>
                    <th className="py-3 pr-4">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {interviews.map((i) => {
                    const rec = i.report?.hiring_recommendation || 'neutral'
                    const recColor =
                      rec === 'no_hire'
                        ? 'bg-red-100 text-red-700'
                        : rec === 'hire' || rec === 'strong_hire'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'

                    return (
                      <tr key={i.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 pr-4">
                          <div className="font-medium text-gray-900">
                            {i.candidate?.full_name || 'Unknown'}
                          </div>
                          <div className="text-xs text-gray-500">{i.candidate?.email}</div>
                        </td>
                        <td className="py-3 pr-4 text-gray-900">{i.job_title || '—'}</td>
                        <td className="py-3 pr-4 text-xs capitalize text-gray-700">{i.status}</td>
                        <td className="py-3 pr-4 text-gray-900">
                          {i.report?.skill_match_score != null
                            ? `${Number(i.report.skill_match_score).toFixed(1)}%`
                            : '—'}
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${recColor}`}>
                            {rec.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-xs text-gray-700 max-w-xs">
                          {i.report?.strengths && i.report.strengths.length > 0
                            ? i.report.strengths.slice(0, 2).join('; ')
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-amber-700 max-w-xs">
                          {i.report?.weaknesses && i.report.weaknesses.length > 0
                            ? i.report.weaknesses.slice(0, 2).join('; ')
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-red-700 max-w-xs">
                          {i.report?.red_flags && i.report.red_flags.length > 0
                            ? i.report.red_flags.slice(0, 2).join('; ')
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs capitalize text-gray-700">
                          {i.report?.experience_level || '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-gray-700 max-w-xs">
                          {i.report?.recommendation_justification
                            ? i.report.recommendation_justification
                            : '—'}
                        </td>
                        <td className="py-3 pr-4 text-xs text-gray-500">
                          {i.created_at ? new Date(i.created_at).toLocaleString() : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </DashboardLayout>
  )
}
