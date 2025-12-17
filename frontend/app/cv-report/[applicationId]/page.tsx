'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { 
  ArrowLeft, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  Lightbulb,
  RefreshCw,
  Award,
  Code,
  MessageSquare,
  Cpu,
  Zap,
  User,
  Briefcase,
  GraduationCap,
  FileCheck,
  BarChart3,
  PieChart,
  Ticket,
  Copy,
  Download,
  Printer
} from 'lucide-react'

// Types
interface CVDetailedScreeningData {
  id: string
  application_id: string
  overall_score: number
  format_score: number
  structure_score: number
  experience_score: number
  education_score: number
  skills_score: number
  language_score: number
  ats_score: number
  impact_score: number
  job_match_score: number
  recommendation: string
  recommendation_reason: string
  top_strengths: string[]
  critical_issues: string[]
  improvement_suggestions: string[]
  format_analysis?: any
  structure_analysis?: any
  experience_analysis?: any
  education_analysis?: any
  skills_analysis?: any
  language_analysis?: any
  ats_analysis?: any
  impact_analysis?: any
  screened_at: string
}

interface Application {
  id: string
  candidate_id: string
  job_description_id: string
  status: string
  candidates?: {
    full_name: string
    email: string
  }
  job_descriptions?: {
    title: string
    id: string
  }
}

// Score Ring Component
function ScoreRing({ 
  score, 
  size = 120, 
  strokeWidth = 10,
  label,
  sublabel,
  dark = false
}: { 
  score: number
  size?: number
  strokeWidth?: number
  label?: string
  sublabel?: string
  dark?: boolean
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference
  
  const getColor = (s: number) => {
    if (s >= 75) return { stroke: '#22c55e', bg: dark ? 'rgba(34,197,94,0.2)' : '#f0fdf4', text: dark ? '#4ade80' : '#15803d' }
    if (s >= 50) return { stroke: '#eab308', bg: dark ? 'rgba(234,179,8,0.2)' : '#fefce8', text: dark ? '#facc15' : '#a16207' }
    return { stroke: '#ef4444', bg: dark ? 'rgba(239,68,68,0.2)' : '#fef2f2', text: dark ? '#f87171' : '#b91c1c' }
  }
  
  const colors = getColor(score)

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={dark ? "rgba(255,255,255,0.1)" : "#e5e7eb"}
            strokeWidth={strokeWidth}
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={colors.stroke}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div 
          className="absolute inset-0 flex flex-col items-center justify-center rounded-full m-2"
          style={{ backgroundColor: colors.bg }}
        >
          <span className="text-3xl font-bold" style={{ color: colors.text }}>{Math.round(score)}</span>
          <span className={`text-xs ${dark ? 'text-gray-400' : 'text-gray-500'}`}>/ 100</span>
        </div>
      </div>
      {label && <p className={`mt-2 text-sm font-semibold ${dark ? 'text-gray-300' : 'text-gray-700'}`}>{label}</p>}
      {sublabel && <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-500'}`}>{sublabel}</p>}
    </div>
  )
}

// Score Bar Component
function ScoreBar({ 
  label, 
  score, 
  icon: Icon
}: { 
  label: string
  score: number
  icon?: React.ComponentType<{ className?: string }>
}) {
  const getColor = (s: number) => {
    if (s >= 75) return 'bg-green-500'
    if (s >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getTextColor = (s: number) => {
    if (s >= 75) return 'text-green-400'
    if (s >= 50) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-4 h-4 text-gray-400" />}
          <span className="font-medium text-gray-300 text-sm">{label}</span>
        </div>
        <span className={`font-bold ${getTextColor(score)}`}>{Math.round(score)}%</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full ${getColor(score)} transition-all duration-700 ease-out`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  )
}

// Recommendation Badge
function RecommendationBadge({ recommendation }: { recommendation: string }) {
  const configs = {
    qualified: {
      icon: CheckCircle,
      label: 'Qualified',
      className: 'bg-green-500/20 text-green-400 border-green-500/30'
    },
    maybe_qualified: {
      icon: AlertTriangle,
      label: 'Maybe Qualified',
      className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
    },
    not_qualified: {
      icon: XCircle,
      label: 'Not Qualified',
      className: 'bg-red-500/20 text-red-400 border-red-500/30'
    }
  }

  const config = configs[recommendation as keyof typeof configs] || configs.maybe_qualified
  const Icon = config.icon

  return (
    <div className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full border ${config.className}`}>
      <Icon className="w-5 h-5" />
      <span className="text-lg font-bold">{config.label}</span>
    </div>
  )
}

// Main Page Component
export default function CVReportPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const applicationId = params.applicationId as string
  const jobId = searchParams.get('jobId')

  const [data, setData] = useState<CVDetailedScreeningData | null>(null)
  const [application, setApplication] = useState<Application | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [creatingTicket, setCreatingTicket] = useState(false)
  const [ticketCode, setTicketCode] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [applicationId])

  const loadData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      // Load application details
      const appResponse = await apiClient.get<Application>(`/applications/${applicationId}`)
      if (appResponse.success && appResponse.data) {
        setApplication(appResponse.data as Application)
      }

      // Load CV analysis
      const response = await apiClient.get<any>(`/cv-screening/result/${applicationId}`)
      
      console.log('CV screening response:', response)

      if (response.success && response.data) {
        let screeningData: CVDetailedScreeningData | null = null
        
        // Handle nested data structure: { success: true, data: { data: {...} } }
        if (response.data.data && typeof response.data.data === 'object' && 'overall_score' in response.data.data) {
          screeningData = response.data.data as CVDetailedScreeningData
        }
        // Handle direct data structure: { success: true, data: {...} }
        else if ('overall_score' in response.data) {
          screeningData = response.data as CVDetailedScreeningData
        }
        // Handle case where data is the full response
        else if (response.data.overall_score) {
          screeningData = response.data as CVDetailedScreeningData
        }
        
        console.log('Parsed screening data:', screeningData)
        setData(screeningData)
      }
    } catch (err: any) {
      console.error('Error loading data:', err)
      if (err.status !== 404) {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const triggerAnalysis = async () => {
    try {
      setAnalyzing(true)
      setError(null)
      
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      await apiClient.post(`/cv-screening/analyze/${applicationId}`)
      
      // Poll for results
      let attempts = 0
      const maxAttempts = 15
      
      const poll = async () => {
        attempts++
        try {
          const response = await apiClient.get<CVDetailedScreeningData | { data: CVDetailedScreeningData | null }>(
            `/cv-screening/result/${applicationId}`
          )
          
          if (response.success && response.data) {
            let screeningData: CVDetailedScreeningData | null = null
            if ('data' in response.data && response.data.data !== undefined) {
              screeningData = response.data.data as CVDetailedScreeningData
            } else if ('overall_score' in response.data) {
              screeningData = response.data as CVDetailedScreeningData
            }
            
            if (screeningData) {
              setData(screeningData)
              setAnalyzing(false)
              return
            }
          }
        } catch {}
        
        if (attempts < maxAttempts) {
          setTimeout(poll, 4000)
        } else {
          setError('Analysis taking longer than expected. Please refresh.')
          setAnalyzing(false)
        }
      }
      
      setTimeout(poll, 3000)
    } catch (err: any) {
      setError(err.message)
      setAnalyzing(false)
    }
  }

  const createInterviewTicket = async () => {
    if (!application) return
    
    try {
      setCreatingTicket(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      const response = await apiClient.post<{ ticket_code: string }>('/tickets', {
        candidate_id: application.candidate_id,
        job_description_id: application.job_description_id
      })

      if (response.success && response.data) {
        setTicketCode((response.data as { ticket_code: string }).ticket_code)
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setCreatingTicket(false)
    }
  }

  const copyTicket = () => {
    if (ticketCode) {
      navigator.clipboard.writeText(ticketCode)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-purple-500/30 border-t-purple-500 mx-auto"></div>
          <p className="mt-6 text-gray-300 text-lg">Loading CV Analysis Report...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 print:bg-white">
      {/* Header Bar */}
      <div className="sticky top-0 z-50 bg-black/30 backdrop-blur-xl border-b border-white/10 print:hidden">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                onClick={() => router.back()}
                className="bg-white/5 border-white/20 text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-purple-400" />
                  CV Analysis Report
                </h1>
                {application && (
                  <p className="text-sm text-gray-400">
                    {application.candidates?.full_name} • {application.job_descriptions?.title}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={handlePrint}
                className="bg-white/5 border-white/20 text-white hover:bg-white/10"
              >
                <Printer className="w-4 h-4 mr-2" />
                Print
              </Button>
              
              {data && (
                <Button
                  variant="outline"
                  onClick={triggerAnalysis}
                  disabled={analyzing}
                  className="bg-white/5 border-white/20 text-white hover:bg-white/10"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${analyzing ? 'animate-spin' : ''}`} />
                  Re-analyze
                </Button>
              )}
              
              {!ticketCode ? (
                <Button
                  variant="primary"
                  onClick={createInterviewTicket}
                  disabled={creatingTicket}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  {creatingTicket ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Ticket className="w-4 h-4 mr-2" />
                      Generate Interview Ticket
                    </>
                  )}
                </Button>
              ) : (
                <div className="flex items-center gap-2 bg-green-500/20 px-4 py-2 rounded-lg border border-green-500/30">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="font-mono font-bold text-green-400">{ticketCode}</span>
                  <button 
                    onClick={copyTicket}
                    className="p-1 hover:bg-white/10 rounded"
                  >
                    <Copy className="w-4 h-4 text-green-400" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300">
            {error}
          </div>
        )}

        {!data ? (
          /* No Analysis Yet */
          <div className="flex flex-col items-center justify-center py-24">
            <div className="w-24 h-24 rounded-full bg-purple-500/20 flex items-center justify-center mb-8">
              <FileText className="w-12 h-12 text-purple-400" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-3">No CV Analysis Yet</h2>
            <p className="text-gray-400 mb-8 max-w-md text-center">
              Run a comprehensive analysis to get detailed insights about this candidate&apos;s CV, 
              including scoring across 8+ categories and AI-powered recommendations.
            </p>
            <Button
              variant="primary"
              size="lg"
              onClick={triggerAnalysis}
              disabled={analyzing}
              className="px-10 py-4 bg-purple-600 hover:bg-purple-700 text-lg"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-5 h-5 mr-3 animate-spin" />
                  Analyzing CV... (20-30 seconds)
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-3" />
                  Run Detailed Analysis
                </>
              )}
            </Button>
          </div>
        ) : (
          /* Full Analysis View */
          <div className="space-y-8">
            {/* Candidate Info Header */}
            <div className="bg-white/5 backdrop-blur rounded-2xl p-6 border border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div className="w-16 h-16 rounded-full bg-purple-500/30 flex items-center justify-center">
                    <User className="w-8 h-8 text-purple-400" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">
                      {application?.candidates?.full_name || 'Unknown Candidate'}
                    </h2>
                    <p className="text-gray-400 flex items-center gap-2 mt-1">
                      <Briefcase className="w-4 h-4" />
                      {application?.job_descriptions?.title || 'Unknown Position'}
                    </p>
                  </div>
                </div>
                <RecommendationBadge recommendation={data.recommendation} />
              </div>
            </div>

            {/* Main Scores Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Overall Score - Large */}
              <div className="lg:col-span-2 bg-white/5 backdrop-blur rounded-2xl p-8 border border-white/10 flex flex-col items-center">
                <ScoreRing 
                  score={data.overall_score} 
                  size={200} 
                  strokeWidth={16}
                  label="Overall CV Score"
                  dark={true}
                />
                {data.recommendation_reason && (
                  <p className="mt-6 text-gray-400 text-center max-w-sm">
                    {data.recommendation_reason}
                  </p>
                )}
              </div>

              {/* Job Match Score */}
              <div className="bg-gradient-to-br from-purple-500/20 to-blue-500/20 backdrop-blur rounded-2xl p-8 border border-purple-500/30 flex flex-col items-center">
                <ScoreRing 
                  score={data.job_match_score} 
                  size={140} 
                  strokeWidth={12}
                  label="Job Match"
                  sublabel="Relevance to position"
                  dark={true}
                />
              </div>

              {/* Quick Stats */}
              <div className="bg-white/5 backdrop-blur rounded-2xl p-6 border border-white/10">
                <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-purple-400" />
                  Quick Stats
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                    <span className="text-gray-300 text-sm">Strengths</span>
                    <span className="text-xl font-bold text-green-400">{data.top_strengths?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                    <span className="text-gray-300 text-sm">Issues</span>
                    <span className="text-xl font-bold text-yellow-400">{data.critical_issues?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                    <span className="text-gray-300 text-sm">Suggestions</span>
                    <span className="text-xl font-bold text-blue-400">{data.improvement_suggestions?.length || 0}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Category Scores */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* All Scores */}
              <div className="bg-white/5 backdrop-blur rounded-2xl p-6 border border-white/10">
                <h3 className="font-bold text-white mb-6 flex items-center gap-2">
                  <PieChart className="w-5 h-5 text-purple-400" />
                  Category Scores
                </h3>
                <div className="space-y-4">
                  <ScoreBar label="Experience" score={data.experience_score} icon={Award} />
                  <ScoreBar label="Skills Match" score={data.skills_score} icon={Code} />
                  <ScoreBar label="ATS Compatibility" score={data.ats_score} icon={Cpu} />
                  <ScoreBar label="Impact" score={data.impact_score} icon={Zap} />
                  <ScoreBar label="Education" score={data.education_score} icon={GraduationCap} />
                  <ScoreBar label="Language" score={data.language_score} icon={MessageSquare} />
                  <ScoreBar label="Format" score={data.format_score} icon={FileCheck} />
                  <ScoreBar label="Structure" score={data.structure_score} icon={FileText} />
                </div>
              </div>

              {/* Strengths & Issues */}
              <div className="space-y-6">
                {data.top_strengths && data.top_strengths.length > 0 && (
                  <div className="bg-green-500/10 backdrop-blur rounded-2xl p-6 border border-green-500/20">
                    <h3 className="font-bold text-green-400 mb-4 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Top Strengths
                    </h3>
                    <ul className="space-y-3">
                      {data.top_strengths.map((strength, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <CheckCircle className="w-4 h-4 text-green-500 mt-1 flex-shrink-0" />
                          <span className="text-gray-300 text-sm">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {data.critical_issues && data.critical_issues.length > 0 && (
                  <div className="bg-yellow-500/10 backdrop-blur rounded-2xl p-6 border border-yellow-500/20">
                    <h3 className="font-bold text-yellow-400 mb-4 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Critical Issues
                    </h3>
                    <ul className="space-y-3">
                      {data.critical_issues.map((issue, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <AlertTriangle className="w-4 h-4 text-yellow-500 mt-1 flex-shrink-0" />
                          <span className="text-gray-300 text-sm">{issue}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Improvement Suggestions */}
            {data.improvement_suggestions && data.improvement_suggestions.length > 0 && (
              <div className="bg-blue-500/10 backdrop-blur rounded-2xl p-6 border border-blue-500/20">
                <h3 className="font-bold text-blue-400 mb-6 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Improvement Suggestions
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.improvement_suggestions.map((suggestion, i) => (
                    <div key={i} className="flex items-start gap-3 p-4 bg-white/5 rounded-xl border border-white/10">
                      <Lightbulb className="w-4 h-4 text-blue-400 mt-1 flex-shrink-0" />
                      <span className="text-gray-300 text-sm">{suggestion}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skills Analysis */}
            {data.skills_analysis && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {data.skills_analysis.matched_skills?.length > 0 && (
                  <div className="bg-white/5 backdrop-blur rounded-2xl p-6 border border-white/10">
                    <h3 className="font-bold text-green-400 mb-4 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Matched Skills
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {data.skills_analysis.matched_skills.map((skill: string, i: number) => (
                        <span key={i} className="px-3 py-1.5 bg-green-500/20 text-green-400 rounded-full text-sm font-medium border border-green-500/30">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {data.skills_analysis.missing_skills?.length > 0 && (
                  <div className="bg-white/5 backdrop-blur rounded-2xl p-6 border border-white/10">
                    <h3 className="font-bold text-red-400 mb-4 flex items-center gap-2">
                      <XCircle className="w-5 h-5" />
                      Missing Skills
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {data.skills_analysis.missing_skills.map((skill: string, i: number) => (
                        <span key={i} className="px-3 py-1.5 bg-red-500/20 text-red-400 rounded-full text-sm font-medium border border-red-500/30">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Experience Stats */}
            {data.experience_analysis && (
              <div className="bg-white/5 backdrop-blur rounded-2xl p-6 border border-white/10">
                <h3 className="font-bold text-white mb-6 flex items-center gap-2">
                  <Award className="w-5 h-5 text-purple-400" />
                  Experience Analysis
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
                    <div className="text-3xl font-bold text-white">{data.experience_analysis.bullet_count || 0}</div>
                    <div className="text-sm text-gray-400">Total Bullets</div>
                  </div>
                  <div className="text-center p-4 bg-green-500/10 rounded-xl border border-green-500/20">
                    <div className="text-3xl font-bold text-green-400">{data.experience_analysis.quantified_bullets || 0}</div>
                    <div className="text-sm text-gray-400">Quantified</div>
                  </div>
                  <div className="text-center p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
                    <div className="text-3xl font-bold text-blue-400">{data.experience_analysis.action_verb_bullets || 0}</div>
                    <div className="text-sm text-gray-400">Action Verbs</div>
                  </div>
                  <div className="text-center p-4 bg-purple-500/10 rounded-xl border border-purple-500/20">
                    <div className="text-3xl font-bold text-purple-400">{data.experience_analysis.found_keywords?.length || 0}</div>
                    <div className="text-sm text-gray-400">Keywords</div>
                  </div>
                </div>
              </div>
            )}

            {/* Footer */}
            <div className="text-center text-sm text-gray-500 py-6 border-t border-white/10">
              Analysis completed: {new Date(data.screened_at).toLocaleString()} | AI Interview Platform
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

