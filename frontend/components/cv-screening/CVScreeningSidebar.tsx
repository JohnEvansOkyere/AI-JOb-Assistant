'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  TrendingUp,
  Lightbulb,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Target,
  Award,
  BookOpen,
  Code,
  MessageSquare,
  Cpu,
  Zap,
  ExternalLink
} from 'lucide-react'

// Score bar component with animated progress
function ScoreBar({ 
  label, 
  score, 
  icon: Icon,
  color = 'primary'
}: { 
  label: string
  score: number
  icon?: React.ComponentType<{ className?: string }>
  color?: 'primary' | 'green' | 'yellow' | 'red' | 'blue' | 'purple'
}) {
  const colorClasses = {
    primary: 'bg-primary-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
  }

  const bgClasses = {
    primary: 'bg-primary-100',
    green: 'bg-green-100',
    yellow: 'bg-yellow-100',
    red: 'bg-red-100',
    blue: 'bg-blue-100',
    purple: 'bg-purple-100',
  }

  const getScoreColor = (s: number) => {
    if (s >= 75) return 'text-green-600'
    if (s >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-1.5">
          {Icon && <Icon className="w-4 h-4 text-gray-500" />}
          <span className="font-medium text-gray-700">{label}</span>
        </div>
        <span className={`font-bold ${getScoreColor(score)}`}>{score}%</span>
      </div>
      <div className={`h-2.5 rounded-full ${bgClasses[color]} overflow-hidden`}>
        <div 
          className={`h-full rounded-full ${colorClasses[color]} transition-all duration-500 ease-out`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  )
}

// Overall score circle component
function OverallScoreCircle({ score }: { score: number }) {
  const getColor = (s: number) => {
    if (s >= 75) return { ring: 'text-green-500', bg: 'bg-green-50', text: 'text-green-700' }
    if (s >= 50) return { ring: 'text-yellow-500', bg: 'bg-yellow-50', text: 'text-yellow-700' }
    return { ring: 'text-red-500', bg: 'bg-red-50', text: 'text-red-700' }
  }

  const colors = getColor(score)
  const circumference = 2 * Math.PI * 45
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg className="w-32 h-32 transform -rotate-90">
          <circle
            cx="64"
            cy="64"
            r="45"
            stroke="currentColor"
            strokeWidth="10"
            fill="none"
            className="text-gray-200"
          />
          <circle
            cx="64"
            cy="64"
            r="45"
            stroke="currentColor"
            strokeWidth="10"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={`${colors.ring} transition-all duration-1000 ease-out`}
          />
        </svg>
        <div className={`absolute inset-0 flex flex-col items-center justify-center ${colors.bg} rounded-full m-3`}>
          <span className={`text-3xl font-bold ${colors.text}`}>{score}</span>
          <span className="text-xs text-gray-500">/ 100</span>
        </div>
      </div>
      <p className="mt-2 text-sm font-medium text-gray-600">Overall CV Score</p>
    </div>
  )
}

// Recommendation badge
function RecommendationBadge({ recommendation }: { recommendation: string }) {
  const configs = {
    qualified: {
      icon: CheckCircle,
      label: 'Qualified',
      className: 'bg-green-100 text-green-800 border-green-200'
    },
    maybe_qualified: {
      icon: AlertTriangle,
      label: 'Maybe Qualified',
      className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
    },
    not_qualified: {
      icon: XCircle,
      label: 'Not Qualified',
      className: 'bg-red-100 text-red-800 border-red-200'
    }
  }

  const config = configs[recommendation as keyof typeof configs] || configs.maybe_qualified
  const Icon = config.icon

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border ${config.className}`}>
      <Icon className="w-5 h-5" />
      <span className="font-semibold">{config.label}</span>
    </div>
  )
}

// Collapsible section
function CollapsibleSection({ 
  title, 
  children, 
  defaultOpen = true 
}: { 
  title: string
  children: React.ReactNode
  defaultOpen?: boolean 
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border-t border-gray-200 pt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left"
      >
        <h4 className="font-semibold text-gray-900">{title}</h4>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>
      {isOpen && <div className="mt-3">{children}</div>}
    </div>
  )
}

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

interface CVScreeningSidebarProps {
  applicationId: string
  onAnalysisComplete?: () => void
}

export function CVScreeningSidebar({ applicationId, onAnalysisComplete }: CVScreeningSidebarProps) {
  const router = useRouter()
  const params = useParams()
  const jobId = params?.id as string
  
  const [data, setData] = useState<CVDetailedScreeningData | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const viewFullReport = () => {
    // Navigate to standalone full report page
    router.push(`/cv-report/${applicationId}${jobId ? `?jobId=${jobId}` : ''}`)
  }

  useEffect(() => {
    loadScreeningData()
  }, [applicationId])

  const loadScreeningData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiClient.setToken(token)
      }

      // Backend returns { success: true, data: screening_data }
      // apiClient wraps this, so we access response.data directly
      const response = await apiClient.get<CVDetailedScreeningData | { data: CVDetailedScreeningData | null }>(
        `/cv-screening/result/${applicationId}`
      )

      // Handle both response formats:
      // 1. { success: true, data: { data: screening_data } } - nested
      // 2. { success: true, data: screening_data } - direct
      let screeningData: CVDetailedScreeningData | null = null
      
      if (response.success && response.data) {
        // Check if data is nested (has 'data' property with the actual data)
        if ('data' in response.data && response.data.data !== undefined) {
          screeningData = response.data.data as CVDetailedScreeningData
        } else if ('overall_score' in response.data) {
          // Direct data format
          screeningData = response.data as CVDetailedScreeningData
        }
      }

      if (screeningData) {
        setData(screeningData)
      } else {
        setData(null)
      }
    } catch (err: any) {
      console.error('Error loading CV screening data:', err)
      // Don't show error for 404 - just means no analysis yet
      if (err.status !== 404) {
        setError(err.message || 'Failed to load screening data')
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
      if (token) {
        apiClient.setToken(token)
      }

      const response = await apiClient.post(`/cv-screening/analyze/${applicationId}`)

      if (response.success) {
        // Poll for results with retries (analysis can take 20-30 seconds)
        let attempts = 0
        const maxAttempts = 12 // 12 attempts * 5 seconds = 60 seconds max wait
        
        const pollForResults = async () => {
          attempts++
          console.log(`Polling for CV analysis results (attempt ${attempts}/${maxAttempts})...`)
          
          try {
            const resultResponse = await apiClient.get<CVDetailedScreeningData | { data: CVDetailedScreeningData | null }>(
              `/cv-screening/result/${applicationId}`
            )
            
            // Handle both response formats
            let screeningData: CVDetailedScreeningData | null = null
            
            if (resultResponse.success && resultResponse.data) {
              if ('data' in resultResponse.data && resultResponse.data.data !== undefined) {
                screeningData = resultResponse.data.data as CVDetailedScreeningData
              } else if ('overall_score' in resultResponse.data) {
                screeningData = resultResponse.data as CVDetailedScreeningData
              }
            }
            
            if (screeningData) {
              // Analysis complete!
              setData(screeningData)
              setAnalyzing(false)
              onAnalysisComplete?.()
              console.log('CV analysis results loaded successfully!')
              return
            }
          } catch (pollError) {
            console.log('Result not ready yet, continuing to poll...')
          }
          
          // If not found yet and we have attempts left, try again
          if (attempts < maxAttempts) {
            setTimeout(pollForResults, 5000) // Wait 5 seconds between polls
          } else {
            // Max attempts reached
            setError('Analysis is taking longer than expected. Please refresh the page.')
            setAnalyzing(false)
          }
        }
        
        // Start polling after initial 3 second delay
        setTimeout(pollForResults, 3000)
      } else {
        setError(response.message || 'Failed to start analysis')
        setAnalyzing(false)
      }
    } catch (err: any) {
      console.error('Error triggering analysis:', err)
      setError(err.message || 'Failed to start analysis')
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <Card className="h-full">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-sm text-gray-600">Loading CV analysis...</p>
        </div>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card className="h-full">
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <FileText className="w-16 h-16 text-gray-300" />
          <div className="text-center">
            <h3 className="font-semibold text-gray-900">No Detailed Analysis Yet</h3>
            <p className="text-sm text-gray-600 mt-1">
              Run a comprehensive CV analysis to see detailed scoring and insights.
            </p>
          </div>
          {analyzing ? (
            <div className="flex flex-col items-center gap-3">
              <div className="relative">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-200 border-t-primary-600"></div>
              </div>
              <div className="text-center">
                <p className="font-medium text-gray-900">Analyzing CV...</p>
                <p className="text-sm text-gray-500 mt-1">This may take 20-30 seconds</p>
              </div>
            </div>
          ) : (
            <Button
              variant="primary"
              onClick={triggerAnalysis}
              className="flex items-center gap-2"
            >
              <Zap className="w-4 h-4" />
              Run Detailed Analysis
            </Button>
          )}
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
        </div>
      </Card>
    )
  }

  return (
    <Card className="h-full overflow-y-auto">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-600" />
            CV Analysis Report
          </h3>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={triggerAnalysis}
              disabled={analyzing}
              title="Re-analyze CV"
            >
              {analyzing ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={viewFullReport}
              className="flex items-center gap-1"
            >
              <ExternalLink className="w-3 h-3" />
              Full Report
            </Button>
          </div>
        </div>

        {/* Overall Score */}
        <div className="flex flex-col items-center py-4 bg-gradient-to-br from-gray-50 to-white rounded-xl border">
          <OverallScoreCircle score={Math.round(data.overall_score)} />
          <div className="mt-4">
            <RecommendationBadge recommendation={data.recommendation} />
          </div>
          {data.recommendation_reason && (
            <p className="mt-3 text-sm text-gray-600 text-center px-4">
              {data.recommendation_reason}
            </p>
          )}
        </div>

        {/* Job Match Score - Highlighted */}
        <div className="bg-primary-50 rounded-lg p-4 border border-primary-200">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary-600" />
              <span className="font-semibold text-primary-800">Job Match Score</span>
            </div>
            <span className="text-2xl font-bold text-primary-600">{Math.round(data.job_match_score)}%</span>
          </div>
          <div className="h-3 bg-primary-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary-600 rounded-full transition-all duration-500"
              style={{ width: `${data.job_match_score}%` }}
            />
          </div>
        </div>

        {/* Category Scores */}
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gray-500" />
            Category Scores
          </h4>
          <div className="space-y-3">
            <ScoreBar label="Experience" score={Math.round(data.experience_score)} icon={Award} color="blue" />
            <ScoreBar label="Skills" score={Math.round(data.skills_score)} icon={Code} color="purple" />
            <ScoreBar label="ATS Compatibility" score={Math.round(data.ats_score)} icon={Cpu} color="green" />
            <ScoreBar label="Impact" score={Math.round(data.impact_score)} icon={Zap} color="yellow" />
            <ScoreBar label="Education" score={Math.round(data.education_score)} icon={BookOpen} color="blue" />
            <ScoreBar label="Language" score={Math.round(data.language_score)} icon={MessageSquare} color="purple" />
            <ScoreBar label="Formatting" score={Math.round(data.format_score)} color="primary" />
            <ScoreBar label="Structure" score={Math.round(data.structure_score)} color="primary" />
          </div>
        </div>

        {/* Strengths */}
        {data.top_strengths && data.top_strengths.length > 0 && (
          <CollapsibleSection title="✅ Top Strengths">
            <ul className="space-y-2">
              {data.top_strengths.map((strength, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </CollapsibleSection>
        )}

        {/* Critical Issues */}
        {data.critical_issues && data.critical_issues.length > 0 && (
          <CollapsibleSection title="⚠️ Critical Issues">
            <ul className="space-y-2">
              {data.critical_issues.map((issue, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{issue}</span>
                </li>
              ))}
            </ul>
          </CollapsibleSection>
        )}

        {/* Improvement Suggestions */}
        {data.improvement_suggestions && data.improvement_suggestions.length > 0 && (
          <CollapsibleSection title="💡 Suggestions" defaultOpen={false}>
            <ul className="space-y-2">
              {data.improvement_suggestions.map((suggestion, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Lightbulb className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{suggestion}</span>
                </li>
              ))}
            </ul>
          </CollapsibleSection>
        )}

        {/* Experience Details */}
        {data.experience_analysis && (
          <CollapsibleSection title="📊 Experience Analysis" defaultOpen={false}>
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-xs text-gray-500">Total Bullets</div>
                  <div className="font-semibold">{data.experience_analysis.bullet_count || 0}</div>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-xs text-gray-500">Quantified</div>
                  <div className="font-semibold">{data.experience_analysis.quantified_bullets || 0}</div>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-xs text-gray-500">Action Verbs</div>
                  <div className="font-semibold">{data.experience_analysis.action_verb_bullets || 0}</div>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <div className="text-xs text-gray-500">Keywords Found</div>
                  <div className="font-semibold">{data.experience_analysis.found_keywords?.length || 0}</div>
                </div>
              </div>
              
              {data.experience_analysis.missing_keywords?.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Missing Keywords</div>
                  <div className="flex flex-wrap gap-1">
                    {data.experience_analysis.missing_keywords.slice(0, 8).map((kw: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 text-xs rounded-full">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CollapsibleSection>
        )}

        {/* Skills Details */}
        {data.skills_analysis && (
          <CollapsibleSection title="🛠️ Skills Analysis" defaultOpen={false}>
            <div className="space-y-3 text-sm">
              {data.skills_analysis.matched_skills?.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Matched Skills</div>
                  <div className="flex flex-wrap gap-1">
                    {data.skills_analysis.matched_skills.map((skill: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {data.skills_analysis.missing_skills?.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Missing Skills</div>
                  <div className="flex flex-wrap gap-1">
                    {data.skills_analysis.missing_skills.slice(0, 8).map((skill: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 text-xs rounded-full">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {data.skills_analysis.technical_skills?.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Technical Skills Found</div>
                  <div className="flex flex-wrap gap-1">
                    {data.skills_analysis.technical_skills.slice(0, 10).map((skill: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CollapsibleSection>
        )}

        {/* Screened At */}
        <div className="text-xs text-gray-400 text-center pt-4 border-t">
          Analyzed: {new Date(data.screened_at).toLocaleString()}
        </div>
      </div>
    </Card>
  )
}

