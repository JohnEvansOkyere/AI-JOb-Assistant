'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import {
  BarChart3,
  RefreshCw,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Meh,
  Clock,
  Search,
  Filter,
  User,
  Briefcase,
  TrendingUp,
  Sparkles
} from 'lucide-react'

interface InterviewReport {
  interview_id: string
  job_id: string
  job_title: string
  candidate_id: string
  candidate_name: string
  candidate_email: string
  completed_at: string
  has_analysis: boolean
  overall_score: number | null
  technical_score: number | null
  soft_skills_score: number | null
  communication_score: number | null
  recommendation: string | null
  recommendation_summary: string | null
  sentiment: string | null
  analyzed_at: string | null
}

interface Job {
  id: string
  title: string
}

function RecommendationBadge({ recommendation }: { recommendation: string | null }) {
  if (!recommendation) return <span className="text-gray-400">-</span>
  
  const configs: Record<string, { bg: string; text: string; label: string }> = {
    strong_hire: { bg: 'bg-green-100', text: 'text-green-800', label: 'Strong Hire' },
    hire: { bg: 'bg-emerald-100', text: 'text-emerald-800', label: 'Hire' },
    maybe: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Maybe' },
    no_hire: { bg: 'bg-red-100', text: 'text-red-800', label: 'No Hire' },
    under_review: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Under Review' },
  }
  
  const config = configs[recommendation] || configs.under_review
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  )
}

function ScoreCell({ score, label }: { score: number | null; label: string }) {
  if (score === null) return <span className="text-gray-400">-</span>
  
  const getColor = (s: number) => {
    if (s >= 75) return 'text-green-600'
    if (s >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }
  
  return (
    <div className="text-center">
      <div className={`font-semibold ${getColor(score)}`}>{Math.round(score)}</div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  )
}

export default function InterviewReportsPage() {
  const router = useRouter()
  const [reports, setReports] = useState<InterviewReport[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedJob, setSelectedJob] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [analyzing, setAnalyzing] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      // Load all interview reports
      const response = await apiClient.get<InterviewReport[]>('/interview-analysis/all-reports')
      if (response.success && response.data) {
        setReports(response.data as InterviewReport[])
        
        // Extract unique jobs
        const uniqueJobs = new Map<string, Job>()
        ;(response.data as InterviewReport[]).forEach(r => {
          if (!uniqueJobs.has(r.job_id)) {
            uniqueJobs.set(r.job_id, { id: r.job_id, title: r.job_title })
          }
        })
        setJobs(Array.from(uniqueJobs.values()))
      }
    } catch (err) {
      console.error('Error loading reports:', err)
    } finally {
      setLoading(false)
    }
  }

  const runAnalysis = async (interviewId: string) => {
    try {
      setAnalyzing(interviewId)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      await apiClient.post(`/interview-analysis/analyze/${interviewId}`)
      
      // Reload data after analysis
      await loadData()
    } catch (err) {
      console.error('Analysis error:', err)
    } finally {
      setAnalyzing(null)
    }
  }

  const filteredReports = reports.filter(r => {
    if (selectedJob && r.job_id !== selectedJob) return false
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      return (
        r.candidate_name.toLowerCase().includes(term) ||
        r.candidate_email.toLowerCase().includes(term) ||
        r.job_title.toLowerCase().includes(term)
      )
    }
    return true
  })

  const stats = {
    total: reports.length,
    analyzed: reports.filter(r => r.has_analysis).length,
    strongHire: reports.filter(r => r.recommendation === 'strong_hire').length,
    hire: reports.filter(r => r.recommendation === 'hire').length,
    maybe: reports.filter(r => r.recommendation === 'maybe').length,
    noHire: reports.filter(r => r.recommendation === 'no_hire').length,
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-purple-600" />
            Interview Reports
          </h1>
          <p className="text-gray-600 mt-1">
            Comprehensive AI analysis of completed interviews
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-xs text-gray-500">Total Interviews</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{stats.analyzed}</div>
            <div className="text-xs text-gray-500">Analyzed</div>
          </Card>
          <Card className="p-4 text-center bg-green-50">
            <div className="text-2xl font-bold text-green-600">{stats.strongHire}</div>
            <div className="text-xs text-green-700">Strong Hire</div>
          </Card>
          <Card className="p-4 text-center bg-emerald-50">
            <div className="text-2xl font-bold text-emerald-600">{stats.hire}</div>
            <div className="text-xs text-emerald-700">Hire</div>
          </Card>
          <Card className="p-4 text-center bg-yellow-50">
            <div className="text-2xl font-bold text-yellow-600">{stats.maybe}</div>
            <div className="text-xs text-yellow-700">Maybe</div>
          </Card>
          <Card className="p-4 text-center bg-red-50">
            <div className="text-2xl font-bold text-red-600">{stats.noHire}</div>
            <div className="text-xs text-red-700">No Hire</div>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by candidate name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="">All Jobs</option>
            {jobs.map(job => (
              <option key={job.id} value={job.id}>{job.title}</option>
            ))}
          </select>
          <Button onClick={loadData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Reports Table */}
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 text-purple-500 animate-spin mx-auto" />
            <p className="mt-2 text-gray-500">Loading reports...</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <Card className="p-12 text-center">
            <BarChart3 className="w-12 h-12 text-gray-300 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No Interview Reports</h3>
            <p className="mt-2 text-gray-500">
              Complete some interviews to see analysis reports here.
            </p>
          </Card>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Candidate</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Overall</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Technical</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Soft Skills</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Comm.</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredReports.map((report) => (
                  <tr key={report.interview_id} className="hover:bg-gray-50">
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{report.candidate_name}</div>
                          <div className="text-sm text-gray-500">{report.candidate_email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-900">{report.job_title}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <ScoreCell score={report.overall_score} label="Score" />
                    </td>
                    <td className="px-4 py-4">
                      <ScoreCell score={report.technical_score} label="Tech" />
                    </td>
                    <td className="px-4 py-4">
                      <ScoreCell score={report.soft_skills_score} label="Soft" />
                    </td>
                    <td className="px-4 py-4">
                      <ScoreCell score={report.communication_score} label="Comm" />
                    </td>
                    <td className="px-4 py-4 text-center">
                      <RecommendationBadge recommendation={report.recommendation} />
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {report.has_analysis ? (
                          <Button
                            size="sm"
                            onClick={() => router.push(`/interview-report/${report.interview_id}`)}
                            className="bg-purple-600 hover:bg-purple-700 text-white"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => runAnalysis(report.interview_id)}
                            disabled={analyzing === report.interview_id}
                          >
                            {analyzing === report.interview_id ? (
                              <>
                                <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <Sparkles className="w-4 h-4 mr-1" />
                                Analyze
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

