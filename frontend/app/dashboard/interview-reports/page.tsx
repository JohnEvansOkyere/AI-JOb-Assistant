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
  Sparkles,
  Download
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
  if (!recommendation) return <span className="text-gray-400 dark:text-gray-500">-</span>
  
  const configs: Record<string, { bg: string; text: string; label: string }> = {
    strong_hire: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-300', label: 'Strong Hire' },
    hire: { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-800 dark:text-emerald-300', label: 'Hire' },
    maybe: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-300', label: 'Maybe' },
    no_hire: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-300', label: 'No Hire' },
    under_review: { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-800 dark:text-gray-300', label: 'Under Review' },
  }
  
  const config = configs[recommendation] || configs.under_review
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  )
}

function ScoreCell({ score, label }: { score: number | null; label: string }) {
  if (score === null) return <span className="text-gray-400 dark:text-gray-500">-</span>
  
  const getColor = (s: number) => {
    if (s >= 75) return 'text-green-600 dark:text-green-400'
    if (s >= 50) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }
  
  return (
    <div className="text-center">
      <div className={`font-semibold ${getColor(score)}`}>{Math.round(score)}</div>
      <div className="text-xs text-gray-400 dark:text-gray-500">{label}</div>
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
  const [selectedRecommendation, setSelectedRecommendation] = useState<string>('')
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
    if (selectedRecommendation && r.recommendation !== selectedRecommendation) return false
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      return (
        r.candidate_name?.toLowerCase().includes(term) ||
        r.candidate_email?.toLowerCase().includes(term) ||
        r.job_title?.toLowerCase().includes(term)
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <BarChart3 className="w-7 h-7 text-purple-600 dark:text-purple-400" />
                Interview Reports
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Comprehensive AI analysis of completed interviews
              </p>
            </div>
            {filteredReports.length > 0 && (
              <Button
                variant="outline"
                onClick={exportToCSV}
                className="flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </Button>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Total Interviews</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">{stats.analyzed}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Analyzed</div>
          </Card>
          <Card className="p-4 text-center bg-green-50 dark:bg-green-900/20">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.strongHire}</div>
            <div className="text-xs text-green-700 dark:text-green-300">Strong Hire</div>
          </Card>
          <Card className="p-4 text-center bg-emerald-50 dark:bg-emerald-900/20">
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{stats.hire}</div>
            <div className="text-xs text-emerald-700 dark:text-emerald-300">Hire</div>
          </Card>
          <Card className="p-4 text-center bg-yellow-50 dark:bg-yellow-900/20">
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.maybe}</div>
            <div className="text-xs text-yellow-700 dark:text-yellow-300">Maybe</div>
          </Card>
          <Card className="p-4 text-center bg-red-50 dark:bg-red-900/20">
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.noHire}</div>
            <div className="text-xs text-red-700 dark:text-red-300">No Hire</div>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              placeholder="Search by candidate name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
            />
          </div>
          <select
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="">All Jobs</option>
            {jobs.map(job => (
              <option key={job.id} value={job.id}>{job.title}</option>
            ))}
          </select>
          <select
            value={selectedRecommendation}
            onChange={(e) => setSelectedRecommendation(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="">All Recommendations</option>
            <option value="strong_hire">Strong Hire</option>
            <option value="hire">Hire</option>
            <option value="maybe">Maybe</option>
            <option value="no_hire">No Hire</option>
            <option value="under_review">Under Review</option>
          </select>
          <Button onClick={loadData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Reports Table */}
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 text-purple-500 dark:text-purple-400 animate-spin mx-auto" />
            <p className="mt-2 text-gray-500 dark:text-gray-400">Loading reports...</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <Card className="p-12 text-center">
            <BarChart3 className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No Interview Reports</h3>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              {searchTerm || selectedJob || selectedRecommendation
                ? 'No reports match your filters.'
                : 'Complete some interviews to see analysis reports here.'}
            </p>
          </Card>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-200 dark:border-gray-700">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Candidate</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Job</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Overall</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Technical</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Soft Skills</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Comm.</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Recommendation</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                {filteredReports.map((report) => (
                  <tr key={report.interview_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{report.candidate_name}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{report.candidate_email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        <span className="text-sm text-gray-900 dark:text-white">{report.job_title}</span>
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

