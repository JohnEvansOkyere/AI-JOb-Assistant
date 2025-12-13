/**
 * Applications Overview Page
 * View all applications across all jobs
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/lib/api/client'

interface Application {
  id: string
  job_description_id: string
  candidate_id: string
  status: string
  applied_at: string
  job_descriptions?: { title: string }
  candidates?: { full_name: string; email: string }
}

export default function ApplicationsPage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
      return
    }

    if (isAuthenticated) {
      // For now, we'll need to get applications from all jobs
      // This is a simplified version - in production, you'd want a dedicated endpoint
      setLoading(false)
    }
  }, [isAuthenticated, authLoading, router])

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
            <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
            <p className="text-gray-600 mt-1">View and manage all job applications</p>
          </div>
          <Button variant="primary" onClick={() => router.push('/dashboard/jobs')}>
            View Jobs
          </Button>
        </div>

        <Card>
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">
              To view applications, please select a job from the Jobs page.
            </p>
            <Button variant="primary" onClick={() => router.push('/dashboard/jobs')}>
              Go to Jobs
            </Button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}

