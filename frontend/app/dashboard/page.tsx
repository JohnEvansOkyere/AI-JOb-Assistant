/**
 * Dashboard Page
 * Main recruiter dashboard
 */

'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

export default function DashboardPage() {
  const router = useRouter()
  const { user, loading, logout, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login')
    }
  }, [loading, isAuthenticated, router])

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  if (loading) {
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            {user && (
              <p className="text-sm text-gray-600">
                Welcome, {user.full_name || user.email}
              </p>
            )}
          </div>
          <Button variant="outline" onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card title="Job Descriptions">
            <p className="text-gray-600 mb-4">Manage your job postings</p>
            <Button variant="primary" onClick={() => router.push('/dashboard/jobs')}>
              View Jobs
            </Button>
          </Card>

          <Card title="Candidates">
            <p className="text-gray-600 mb-4">View candidate applications</p>
            <Button variant="primary" onClick={() => router.push('/dashboard/candidates')}>
              View Candidates
            </Button>
          </Card>

          <Card title="Interviews">
            <p className="text-gray-600 mb-4">Monitor interview sessions</p>
            <Button variant="primary" onClick={() => router.push('/dashboard/interviews')}>
              View Interviews
            </Button>
          </Card>
        </div>

        <div className="mt-8">
          <Card title="Quick Actions">
            <div className="space-y-4">
              <Button
                variant="primary"
                onClick={() => router.push('/dashboard/jobs/new')}
                className="w-full"
              >
                Create New Job Description
              </Button>
            </div>
          </Card>
        </div>
      </main>
    </div>
  )
}

