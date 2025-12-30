/**
 * Interview Replay Page
 * View and replay interview sessions with audio playback
 */

'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { apiClient } from '@/lib/api/client'
import { ArrowLeft, User, Briefcase, Calendar, Clock, Play, Pause } from 'lucide-react'
import { formatDateReadable } from '@/lib/utils/date'
import { AudioPlayer } from '@/components/interview/AudioPlayer'

interface QnAItem {
  question_id: string
  question_text: string
  question_order: number
  question_type?: string
  response_text: string
  response_audio_path?: string
  response_audio_url?: string
  response_created_at?: string
}

interface ReplayData {
  interview_id: string
  interview_status: string
  interview_mode: string
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  candidate: {
    id: string
    full_name: string
    email: string
  }
  job: {
    id: string
    title: string
  }
  questions_and_responses: QnAItem[]
}

export default function InterviewReplayPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const interviewId = params.interviewId as string

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [replayData, setReplayData] = useState<ReplayData | null>(null)

  useEffect(() => {
    if (!user) return

    const fetchReplayData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const token = localStorage.getItem('auth_token')
        if (token) {
          apiClient.setToken(token)
        }

        const response = await apiClient.get<ReplayData>(`/interviews/${interviewId}/replay`)
        
        if (response.success && response.data) {
          setReplayData(response.data)
        } else {
          setError(response.message || 'Failed to load interview replay')
        }
      } catch (err: any) {
        console.error('Error fetching interview replay:', err)
        setError(err.message || 'Failed to load interview replay')
      } finally {
        setLoading(false)
      }
    }

    fetchReplayData()
  }, [user, interviewId])

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading interview replay...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error || !replayData) {
    return (
      <DashboardLayout>
        <div className="max-w-4xl mx-auto py-8 px-4">
          <Button
            variant="secondary"
            onClick={() => router.back()}
            className="mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Card className="p-6">
            <div className="text-center">
              <p className="text-red-600 dark:text-red-400 mb-4">{error || 'Interview replay not found'}</p>
              <Button onClick={() => router.back()}>Go Back</Button>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="secondary"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Interviews
          </Button>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Interview Replay
          </h1>
        </div>

        {/* Interview Info */}
        <Card className="p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-2">
                <User className="w-5 h-5" />
                <span className="font-medium">Candidate</span>
              </div>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {replayData.candidate.full_name}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {replayData.candidate.email}
              </p>
            </div>

            <div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-2">
                <Briefcase className="w-5 h-5" />
                <span className="font-medium">Job Position</span>
              </div>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {replayData.job.title}
              </p>
            </div>

            <div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-2">
                <Calendar className="w-5 h-5" />
                <span className="font-medium">Date</span>
              </div>
              <p className="text-gray-900 dark:text-white">
                {replayData.started_at ? formatDateReadable(replayData.started_at) : 'N/A'}
              </p>
            </div>

            <div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-2">
                <Clock className="w-5 h-5" />
                <span className="font-medium">Duration</span>
              </div>
              <p className="text-gray-900 dark:text-white">
                {formatDuration(replayData.duration_seconds)}
              </p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {replayData.interview_mode === 'voice' ? 'Voice Interview' : 'Text Interview'}
            </span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ml-2 ${
              replayData.interview_status === 'completed' 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
            }`}>
              {replayData.interview_status}
            </span>
          </div>
        </Card>

        {/* Questions and Responses */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Interview Q&A
          </h2>

          {replayData.questions_and_responses.length === 0 ? (
            <Card className="p-6">
              <p className="text-gray-600 dark:text-gray-400 text-center">
                No questions and responses found for this interview.
              </p>
            </Card>
          ) : (
            replayData.questions_and_responses.map((qa, index) => (
              <Card key={qa.question_id} className="p-6">
                <div className="space-y-4">
                  {/* Question */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 font-semibold">
                        {qa.question_order}
                      </span>
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Question {qa.question_order}
                      </span>
                    </div>
                    <p className="text-lg text-gray-900 dark:text-white whitespace-pre-wrap">
                      {qa.question_text}
                    </p>
                  </div>

                  {/* Response */}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <div className="mb-2">
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        Candidate Response
                      </span>
                    </div>
                    
                    {/* Transcript */}
                    <div className="mb-4">
                      <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                        {qa.response_text || 'No response text available'}
                      </p>
                    </div>

                    {/* Audio Player (if available) */}
                    {qa.response_audio_url && replayData.interview_mode === 'voice' && (
                      <div className="mt-4">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                          Audio Response
                        </p>
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                          <AudioPlayer
                            audioUrl={qa.response_audio_url}
                            autoPlay={false}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}

