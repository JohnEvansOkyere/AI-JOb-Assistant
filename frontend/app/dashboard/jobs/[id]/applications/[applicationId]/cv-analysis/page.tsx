'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { 
  ArrowLeft, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  TrendingUp,
  Lightbulb,
  RefreshCw,
  Target,
  Award,
  BookOpen,
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
  Ticket
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
  }
}

// Score Ring Component
function ScoreRing({ 
  score, 
  size = 120, 
  strokeWidth = 10,
  label,
  sublabel
}: { 
  score: number
  size?: number
  strokeWidth?: number
  label?: string
  sublabel?: string
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference
  
  const getColor = (s: number) => {
    if (s >= 75) return { stroke: '#22c55e', bg: '#f0fdf4', text: '#15803d' }
    if (s >= 50) return { stroke: '#eab308', bg: '#fefce8', text: '#a16207' }
    return { stroke: '#ef4444', bg: '#fef2f2', text: '#b91c1c' }
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
            stroke="#e5e7eb"
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
          <span className="text-xs text-gray-500">/ 100</span>
        </div>
      </div>
      {label && <p className="mt-2 text-sm font-semibold text-gray-700">{label}</p>}
      {sublabel && <p className="text-xs text-gray-500">{sublabel}</p>}
    </div>
  )
}

// Score Bar Component
function ScoreBar({ 
  label, 
  score, 
  icon: Icon,
  showDetails = false,
  details
}: { 
  label: string
  score: number
  icon?: React.ComponentType<{ className?: string }>
  showDetails?: boolean
  details?: string
}) {
  const getColor = (s: number) => {
    if (s >= 75) return 'bg-green-500'
    if (s >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getTextColor = (s: number) => {
    if (s >= 75) return 'text-green-600'
    if (s >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-5 h-5 text-gray-500" />}
          <span className="font-medium text-gray-700">{label}</span>
        </div>
        <span className={`text-lg font-bold ${getTextColor(score)}`}>{Math.round(score)}%</span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full ${getColor(score)} transition-all duration-700 ease-out`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
      {showDetails && details && (
        <p className="text-xs text-gray-500 mt-1">{details}</p>
      )}
    </div>
  )
}

// Recommendation Badge
function RecommendationBadge({ recommendation, size = 'large' }: { recommendation: string, size?: 'small' | 'large' }) {
  const configs = {
    qualified: {
      icon: CheckCircle,
      label: 'Qualified',
      className: 'bg-green-100 text-green-800 border-green-300'
    },
    maybe_qualified: {
      icon: AlertTriangle,
      label: 'Maybe Qualified',
      className: 'bg-yellow-100 text-yellow-800 border-yellow-300'
    },
    not_qualified: {
      icon: XCircle,
      label: 'Not Qualified',
      className: 'bg-red-100 text-red-800 border-red-300'
    }
  }

  const config = configs[recommendation as keyof typeof configs] || configs.maybe_qualified
  const Icon = config.icon

  if (size === 'small') {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border text-sm ${config.className}`}>
        <Icon className="w-4 h-4" />
        {config.label}
      </span>
    )
  }

  return (
    <div className={`inline-flex items-center gap-3 px-6 py-3 rounded-xl border-2 ${config.className}`}>
      <Icon className="w-8 h-8" />
      <div>
        <span className="text-xl font-bold">{config.label}</span>
      </div>
    </div>
  )
}

// Section Card Component
function SectionCard({ 
  title, 
  icon: Icon, 
  children,
  className = ''
}: { 
  title: string
  icon: React.ComponentType<{ className?: string }>
  children: React.ReactNode
  className?: string
}) {
  return (
    <Card className={`p-6 ${className}`}>
      <h3 className="flex items-center gap-2 text-lg font-bold text-gray-900 mb-4">
        <Icon className="w-5 h-5 text-primary-600" />
        {title}
      </h3>
      {children}
    </Card>
  )
}

// Main Page Component
export default function CVAnalysisPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string
  const applicationId = params.applicationId as string

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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading CV Analysis...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="outline"
            onClick={() => router.back()}
            className="mb-4 bg-white/10 border-white/20 text-white hover:bg-white/20"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Application
          </Button>
          
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <FileText className="w-8 h-8 text-primary-600" />
                CV Analysis Report
              </h1>
              {application && (
                <div className="mt-2 text-gray-600">
                  <p className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    {application.candidates?.full_name || 'Unknown Candidate'}
                  </p>
                  <p className="flex items-center gap-2 mt-1">
                    <Briefcase className="w-4 h-4" />
                    {application.job_descriptions?.title || 'Unknown Position'}
                  </p>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              {data && (
                <Button
                  variant="outline"
                  onClick={triggerAnalysis}
                  disabled={analyzing}
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
                <div className="flex items-center gap-2 bg-green-50 px-4 py-2 rounded-lg border border-green-200">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-mono font-bold text-green-800">{ticketCode}</span>
                  <Button variant="outline" size="sm" onClick={copyTicket}>
                    Copy
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {!data ? (
          /* No Analysis Yet */
          <Card className="p-12 text-center">
            <FileText className="w-20 h-20 text-gray-300 mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No CV Analysis Yet</h2>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Run a comprehensive analysis to get detailed insights about this candidate&apos;s CV, 
              including scoring across 8+ categories and AI-powered recommendations.
            </p>
            <Button
              variant="primary"
              size="lg"
              onClick={triggerAnalysis}
              disabled={analyzing}
              className="px-8"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing CV... (20-30 seconds)
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-2" />
                  Run Detailed Analysis
                </>
              )}
            </Button>
          </Card>
        ) : (
          /* Full Analysis View */
          <div className="space-y-8">
            {/* Top Summary Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Overall Score Card */}
              <Card className="p-8 flex flex-col items-center justify-center bg-gradient-to-br from-white to-gray-50">
                <ScoreRing 
                  score={data.overall_score} 
                  size={160} 
                  strokeWidth={14}
                  label="Overall CV Score"
                />
                <div className="mt-6">
                  <RecommendationBadge recommendation={data.recommendation} />
                </div>
                {data.recommendation_reason && (
                  <p className="mt-4 text-sm text-gray-600 text-center max-w-xs">
                    {data.recommendation_reason}
                  </p>
                )}
              </Card>

              {/* Job Match Card */}
              <Card className="p-8 flex flex-col items-center justify-center bg-gradient-to-br from-primary-50 to-white border-primary-200">
                <ScoreRing 
                  score={data.job_match_score} 
                  size={140} 
                  strokeWidth={12}
                  label="Job Match Score"
                  sublabel="Relevance to position"
                />
                <div className="mt-4 w-full">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Not Relevant</span>
                    <span>Perfect Match</span>
                  </div>
                </div>
              </Card>

              {/* Quick Stats Card */}
              <Card className="p-6">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-primary-600" />
                  Quick Stats
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Strengths Found</span>
                    <span className="text-xl font-bold text-green-600">{data.top_strengths?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Issues to Address</span>
                    <span className="text-xl font-bold text-yellow-600">{data.critical_issues?.length || 0}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-gray-600">Suggestions</span>
                    <span className="text-xl font-bold text-blue-600">{data.improvement_suggestions?.length || 0}</span>
                  </div>
                </div>
              </Card>
            </div>

            {/* Category Scores Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <SectionCard title="Experience" icon={Award}>
                <ScoreRing score={data.experience_score} size={100} strokeWidth={8} />
                <div className="mt-4 text-sm text-gray-600">
                  {data.experience_analysis?.bullet_count > 0 && (
                    <p>{data.experience_analysis.bullet_count} bullet points analyzed</p>
                  )}
                  {data.experience_analysis?.quantified_bullets > 0 && (
                    <p>{data.experience_analysis.quantified_bullets} with metrics</p>
                  )}
                </div>
              </SectionCard>

              <SectionCard title="Skills" icon={Code}>
                <ScoreRing score={data.skills_score} size={100} strokeWidth={8} />
                <div className="mt-4 text-sm text-gray-600">
                  {data.skills_analysis?.matched_skills?.length > 0 && (
                    <p>{data.skills_analysis.matched_skills.length} skills matched</p>
                  )}
                  {data.skills_analysis?.missing_skills?.length > 0 && (
                    <p className="text-yellow-600">{data.skills_analysis.missing_skills.length} missing</p>
                  )}
                </div>
              </SectionCard>

              <SectionCard title="ATS Score" icon={Cpu}>
                <ScoreRing score={data.ats_score} size={100} strokeWidth={8} />
                <div className="mt-4 text-sm text-gray-600">
                  {data.ats_analysis?.ats_friendly ? (
                    <p className="text-green-600">✓ ATS Friendly</p>
                  ) : (
                    <p className="text-yellow-600">⚠ May have ATS issues</p>
                  )}
                </div>
              </SectionCard>

              <SectionCard title="Impact" icon={Zap}>
                <ScoreRing score={data.impact_score} size={100} strokeWidth={8} />
                <div className="mt-4 text-sm text-gray-600">
                  <p>Clarity, professionalism & uniqueness</p>
                </div>
              </SectionCard>
            </div>

            {/* Detailed Scores */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SectionCard title="All Category Scores" icon={PieChart}>
                <div className="space-y-5">
                  <ScoreBar label="Experience" score={data.experience_score} icon={Award} />
                  <ScoreBar label="Skills Match" score={data.skills_score} icon={Code} />
                  <ScoreBar label="ATS Compatibility" score={data.ats_score} icon={Cpu} />
                  <ScoreBar label="Impact" score={data.impact_score} icon={Zap} />
                  <ScoreBar label="Education" score={data.education_score} icon={GraduationCap} />
                  <ScoreBar label="Language Quality" score={data.language_score} icon={MessageSquare} />
                  <ScoreBar label="Formatting" score={data.format_score} icon={FileCheck} />
                  <ScoreBar label="Structure" score={data.structure_score} icon={FileText} />
                </div>
              </SectionCard>

              <div className="space-y-6">
                {/* Strengths */}
                {data.top_strengths && data.top_strengths.length > 0 && (
                  <SectionCard title="Top Strengths" icon={CheckCircle} className="border-green-200 bg-green-50/30">
                    <ul className="space-y-3">
                      {data.top_strengths.map((strength, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-700">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </SectionCard>
                )}

                {/* Critical Issues */}
                {data.critical_issues && data.critical_issues.length > 0 && (
                  <SectionCard title="Critical Issues" icon={AlertTriangle} className="border-yellow-200 bg-yellow-50/30">
                    <ul className="space-y-3">
                      {data.critical_issues.map((issue, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-700">{issue}</span>
                        </li>
                      ))}
                    </ul>
                  </SectionCard>
                )}
              </div>
            </div>

            {/* Improvement Suggestions */}
            {data.improvement_suggestions && data.improvement_suggestions.length > 0 && (
              <SectionCard title="Improvement Suggestions" icon={Lightbulb} className="border-blue-200 bg-blue-50/30">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.improvement_suggestions.map((suggestion, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-blue-100">
                      <Lightbulb className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700 text-sm">{suggestion}</span>
                    </div>
                  ))}
                </div>
              </SectionCard>
            )}

            {/* Skills Analysis Detail */}
            {data.skills_analysis && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {data.skills_analysis.matched_skills?.length > 0 && (
                  <SectionCard title="Matched Skills" icon={CheckCircle}>
                    <div className="flex flex-wrap gap-2">
                      {data.skills_analysis.matched_skills.map((skill: string, i: number) => (
                        <span key={i} className="px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </SectionCard>
                )}

                {data.skills_analysis.missing_skills?.length > 0 && (
                  <SectionCard title="Missing Skills" icon={XCircle}>
                    <div className="flex flex-wrap gap-2">
                      {data.skills_analysis.missing_skills.map((skill: string, i: number) => (
                        <span key={i} className="px-3 py-1.5 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </SectionCard>
                )}
              </div>
            )}

            {/* Experience Analysis Detail */}
            {data.experience_analysis && (
              <SectionCard title="Experience Analysis Details" icon={Award}>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-3xl font-bold text-gray-900">{data.experience_analysis.bullet_count || 0}</div>
                    <div className="text-sm text-gray-600">Total Bullets</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-3xl font-bold text-green-600">{data.experience_analysis.quantified_bullets || 0}</div>
                    <div className="text-sm text-gray-600">Quantified</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-3xl font-bold text-blue-600">{data.experience_analysis.action_verb_bullets || 0}</div>
                    <div className="text-sm text-gray-600">Action Verbs</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-3xl font-bold text-purple-600">{data.experience_analysis.found_keywords?.length || 0}</div>
                    <div className="text-sm text-gray-600">Keywords</div>
                  </div>
                </div>

                {/* Strong Bullets */}
                {data.experience_analysis.strong_bullets?.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-semibold text-green-700 mb-3">✓ Strong Bullet Points</h4>
                    <ul className="space-y-2">
                      {data.experience_analysis.strong_bullets.slice(0, 3).map((bullet: string, i: number) => (
                        <li key={i} className="p-3 bg-green-50 rounded-lg text-sm text-gray-700 border-l-4 border-green-400">
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Weak Bullets */}
                {data.experience_analysis.weak_bullets?.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-semibold text-yellow-700 mb-3">⚠ Could Be Improved</h4>
                    <ul className="space-y-2">
                      {data.experience_analysis.weak_bullets.slice(0, 3).map((bullet: string, i: number) => (
                        <li key={i} className="p-3 bg-yellow-50 rounded-lg text-sm text-gray-700 border-l-4 border-yellow-400">
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </SectionCard>
            )}

            {/* Footer */}
            <div className="text-center text-sm text-gray-500 py-6 border-t">
              Analysis completed: {new Date(data.screened_at).toLocaleString()} | Version: 1.0
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

