'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { 
  ArrowLeft, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  Lightbulb,
  RefreshCw,
  Award,
  MessageSquare,
  User,
  Briefcase,
  Brain,
  Heart,
  Users,
  Target,
  Sparkles,
  Clock,
  Shield,
  Smile,
  Frown,
  Meh,
  TrendingUp,
  Quote,
  ThumbsUp,
  ThumbsDown,
  Printer,
  BarChart3
} from 'lucide-react'

// Types
interface InterviewAnalysisData {
  id: string
  interview_id: string
  overall_score: number
  technical_score: number
  soft_skills_score: number
  communication_score: number
  
  // Soft skills
  leadership_score: number
  teamwork_score: number
  problem_solving_score: number
  adaptability_score: number
  creativity_score: number
  emotional_intelligence_score: number
  time_management_score: number
  conflict_resolution_score: number
  
  // Communication
  clarity_score: number
  articulation_score: number
  confidence_score: number
  listening_score: number
  persuasion_score: number
  
  // Technical
  technical_depth_score: number
  technical_breadth_score: number
  practical_application_score: number
  industry_knowledge_score: number
  
  // Sentiment
  overall_sentiment: string
  sentiment_score: number
  enthusiasm_level: string
  stress_indicators: string[]
  
  // Behavioral
  honesty_indicators: string[]
  red_flag_behaviors: string[]
  positive_behaviors: string[]
  
  // Analysis JSON
  soft_skills_analysis: any
  technical_analysis: any
  communication_analysis: any
  sentiment_analysis: any
  behavioral_analysis: any
  question_analyses: any[]
  
  // Summary
  key_strengths: string[]
  areas_for_improvement: string[]
  notable_quotes: string[]
  follow_up_topics: string[]
  
  // Fit
  culture_fit_score: number
  culture_fit_notes: string
  role_fit_score: number
  role_fit_analysis: string
  
  // Recommendation
  recommendation: string
  recommendation_confidence: number
  recommendation_summary: string
  detailed_recommendation: string
  
  // Metadata
  total_questions: number
  total_responses: number
  average_response_length: number
  analyzed_at: string
}

interface Interview {
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
            fill="none"
            stroke={dark ? 'rgba(255,255,255,0.1)' : '#e5e7eb'}
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={colors.stroke}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>
            {Math.round(score)}
          </span>
          <span className={`text-xs ${dark ? 'text-gray-400' : 'text-gray-500'}`}>/ 100</span>
        </div>
      </div>
      {label && (
        <div className="mt-2 text-center">
          <p className={`font-medium ${dark ? 'text-white' : 'text-gray-900'}`}>{label}</p>
          {sublabel && <p className={`text-xs ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{sublabel}</p>}
        </div>
      )}
    </div>
  )
}

// Score Bar Component
function ScoreBar({ label, score, icon: Icon }: { label: string; score: number; icon?: any }) {
  const getBarColor = (s: number) => {
    if (s >= 75) return 'bg-green-500'
    if (s >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-4 h-4 text-purple-400" />}
          <span className="text-sm text-gray-300">{label}</span>
        </div>
        <span className="text-sm font-medium text-white">{Math.round(score)}</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${getBarColor(score)} rounded-full transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}

// Recommendation Badge
function RecommendationBadge({ recommendation, confidence }: { recommendation: string; confidence: number }) {
  const configs: Record<string, { bg: string; text: string; icon: any; label: string }> = {
    strong_hire: { bg: 'bg-green-500/20', text: 'text-green-400', icon: ThumbsUp, label: 'Strong Hire' },
    hire: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: CheckCircle, label: 'Hire' },
    maybe: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: Meh, label: 'Maybe' },
    no_hire: { bg: 'bg-red-500/20', text: 'text-red-400', icon: ThumbsDown, label: 'No Hire' },
    under_review: { bg: 'bg-gray-500/20', text: 'text-gray-400', icon: Clock, label: 'Under Review' },
  }
  
  const config = configs[recommendation] || configs.under_review
  const Icon = config.icon
  
  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${config.bg}`}>
      <Icon className={`w-5 h-5 ${config.text}`} />
      <span className={`font-medium ${config.text}`}>{config.label}</span>
      <span className="text-gray-400 text-sm">({Math.round(confidence)}% confidence)</span>
    </div>
  )
}

// Sentiment Indicator
function SentimentIndicator({ sentiment, score, enthusiasm }: { sentiment: string; score: number; enthusiasm: string }) {
  const sentimentConfigs: Record<string, { icon: any; color: string; label: string }> = {
    positive: { icon: Smile, color: 'text-green-400', label: 'Positive' },
    neutral: { icon: Meh, color: 'text-yellow-400', label: 'Neutral' },
    negative: { icon: Frown, color: 'text-red-400', label: 'Negative' },
    mixed: { icon: TrendingUp, color: 'text-purple-400', label: 'Mixed' },
  }
  
  const config = sentimentConfigs[sentiment] || sentimentConfigs.neutral
  const Icon = config.icon
  
  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <Icon className={`w-6 h-6 ${config.color}`} />
        <span className="text-white font-medium">{config.label}</span>
      </div>
      <div className="text-gray-400">|</div>
      <div className="text-gray-300">
        Enthusiasm: <span className="text-white font-medium capitalize">{enthusiasm}</span>
      </div>
    </div>
  )
}

export default function InterviewReportPage() {
  const params = useParams()
  const router = useRouter()
  const interviewId = params.interviewId as string
  
  const [interview, setInterview] = useState<Interview | null>(null)
  const [data, setData] = useState<InterviewAnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [interviewId])

  const loadData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (token) apiClient.setToken(token)

      // Load interview details
      const interviewResponse = await apiClient.get<any>(`/interviews/${interviewId}`)
      if (interviewResponse.success && interviewResponse.data) {
        setInterview(interviewResponse.data as Interview)
      }

      // Load analysis
      const response = await apiClient.get<any>(`/interview-analysis/result/${interviewId}`)
      
      if (response.success && response.data) {
        let analysisData: InterviewAnalysisData | null = null
        
        if (response.data.data && typeof response.data.data === 'object' && 'overall_score' in response.data.data) {
          analysisData = response.data.data as InterviewAnalysisData
        } else if ('overall_score' in response.data) {
          analysisData = response.data as InterviewAnalysisData
        }
        
        setData(analysisData)
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

      await apiClient.post(`/interview-analysis/analyze/${interviewId}`)
      
      // Poll for results
      let attempts = 0
      const maxAttempts = 24 // Up to 2 minutes
      
      const pollForResults = async () => {
        attempts++
        console.log(`Polling for analysis results (attempt ${attempts}/${maxAttempts})...`)
        
        try {
          const resultResponse = await apiClient.get<any>(`/interview-analysis/result/${interviewId}`)
          
          if (resultResponse.success && resultResponse.data) {
            let analysisData: InterviewAnalysisData | null = null
            
            if (resultResponse.data.data && typeof resultResponse.data.data === 'object') {
              analysisData = resultResponse.data.data as InterviewAnalysisData
            } else if ('overall_score' in resultResponse.data) {
              analysisData = resultResponse.data as InterviewAnalysisData
            }
            
            if (analysisData) {
              setData(analysisData)
              setAnalyzing(false)
              return
            }
          }
        } catch (pollError) {
          console.log('Result not ready yet, continuing to poll...')
        }
        
        if (attempts < maxAttempts) {
          setTimeout(pollForResults, 5000)
        } else {
          setError('Analysis is taking longer than expected. Please refresh the page.')
          setAnalyzing(false)
        }
      }
      
      setTimeout(pollForResults, 5000)
      
    } catch (err: any) {
      console.error('Analysis error:', err)
      setError(err.message || 'Failed to start analysis')
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-purple-400 animate-spin mx-auto" />
          <p className="mt-4 text-gray-300">Loading interview report...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-8">
        <div className="max-w-4xl mx-auto">
          <Button
            variant="outline"
            onClick={() => router.back()}
            className="text-gray-300 hover:text-white mb-8 border-gray-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          
          <div className="text-center py-16">
            <BarChart3 className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">No Analysis Yet</h2>
            <p className="text-gray-400 mb-8 max-w-md mx-auto">
              Run a comprehensive analysis to get detailed insights about this interview,
              including soft skills, technical assessment, sentiment analysis, and hiring recommendation.
            </p>
            
            <Button
              onClick={triggerAnalysis}
              disabled={analyzing}
              className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-3"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing... (this may take 1-2 minutes)
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Run Detailed Analysis
                </>
              )}
            </Button>
            
            {error && (
              <p className="mt-4 text-red-400">{error}</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 print:bg-white">
      {/* Header */}
      <div className="bg-black/30 border-b border-purple-500/20 print:bg-white print:border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                onClick={() => router.back()}
                className="text-gray-300 hover:text-white print:hidden border-gray-600"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-xl font-bold text-white print:text-gray-900">
                  Interview Analysis Report
                </h1>
                <p className="text-gray-400 text-sm print:text-gray-600">
                  {interview?.candidates?.full_name || 'Candidate'} • {interview?.job_descriptions?.title || 'Position'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 print:hidden">
              <Button
                variant="outline"
                onClick={() => window.print()}
                className="border-purple-500/50 text-purple-300 hover:bg-purple-500/20"
              >
                <Printer className="w-4 h-4 mr-2" />
                Print
              </Button>
              <Button
                onClick={triggerAnalysis}
                disabled={analyzing}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                {analyzing ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                Re-analyze
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        
        {/* Overview Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Scores */}
          <div className="lg:col-span-2 bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-6">Overall Assessment</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <ScoreRing score={data.overall_score} label="Overall" sublabel="Score" dark />
              <ScoreRing score={data.technical_score} label="Technical" sublabel="Skills" dark />
              <ScoreRing score={data.soft_skills_score} label="Soft Skills" dark />
              <ScoreRing score={data.communication_score} label="Communication" dark />
            </div>
          </div>
          
          {/* Recommendation */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4">Recommendation</h2>
            <div className="mb-4">
              <RecommendationBadge 
                recommendation={data.recommendation} 
                confidence={data.recommendation_confidence} 
              />
            </div>
            <p className="text-gray-300 text-sm">{data.recommendation_summary}</p>
          </div>
        </div>

        {/* Sentiment & Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sentiment */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4">Sentiment Analysis</h2>
            <SentimentIndicator 
              sentiment={data.overall_sentiment}
              score={data.sentiment_score}
              enthusiasm={data.enthusiasm_level}
            />
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Culture Fit</p>
                <div className="flex items-center gap-2">
                  <Heart className="w-5 h-5 text-pink-400" />
                  <span className="text-2xl font-bold text-white">{Math.round(data.culture_fit_score)}</span>
                </div>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Role Fit</p>
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-400" />
                  <span className="text-2xl font-bold text-white">{Math.round(data.role_fit_score)}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Interview Stats */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4">Interview Statistics</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-400">{data.total_questions}</p>
                <p className="text-xs text-gray-400">Questions</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-400">{data.total_responses}</p>
                <p className="text-xs text-gray-400">Responses</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-400">{data.average_response_length}</p>
                <p className="text-xs text-gray-400">Avg Words</p>
              </div>
            </div>
          </div>
        </div>

        {/* Soft Skills Breakdown */}
        <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
          <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Soft Skills Assessment
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <ScoreBar label="Leadership" score={data.leadership_score} icon={Award} />
            <ScoreBar label="Teamwork" score={data.teamwork_score} icon={Users} />
            <ScoreBar label="Problem Solving" score={data.problem_solving_score} icon={Brain} />
            <ScoreBar label="Adaptability" score={data.adaptability_score} icon={TrendingUp} />
            <ScoreBar label="Creativity" score={data.creativity_score} icon={Sparkles} />
            <ScoreBar label="Emotional Intelligence" score={data.emotional_intelligence_score} icon={Heart} />
            <ScoreBar label="Time Management" score={data.time_management_score} icon={Clock} />
            <ScoreBar label="Conflict Resolution" score={data.conflict_resolution_score} icon={Shield} />
          </div>
        </div>

        {/* Communication & Technical */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Communication */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-purple-400" />
              Communication Skills
            </h2>
            <div className="space-y-4">
              <ScoreBar label="Clarity" score={data.clarity_score} />
              <ScoreBar label="Articulation" score={data.articulation_score} />
              <ScoreBar label="Confidence" score={data.confidence_score} />
              <ScoreBar label="Listening" score={data.listening_score} />
              <ScoreBar label="Persuasion" score={data.persuasion_score} />
            </div>
          </div>
          
          {/* Technical */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" />
              Technical Assessment
            </h2>
            <div className="space-y-4">
              <ScoreBar label="Technical Depth" score={data.technical_depth_score} />
              <ScoreBar label="Technical Breadth" score={data.technical_breadth_score} />
              <ScoreBar label="Practical Application" score={data.practical_application_score} />
              <ScoreBar label="Industry Knowledge" score={data.industry_knowledge_score} />
            </div>
          </div>
        </div>

        {/* Key Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Strengths */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              Key Strengths
            </h2>
            {data.key_strengths && data.key_strengths.length > 0 ? (
              <ul className="space-y-2">
                {data.key_strengths.map((strength, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-300">
                    <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                    {strength}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No strengths identified yet</p>
            )}
          </div>
          
          {/* Areas for Improvement */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
              Areas for Improvement
            </h2>
            {data.areas_for_improvement && data.areas_for_improvement.length > 0 ? (
              <ul className="space-y-2">
                {data.areas_for_improvement.map((area, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-300">
                    <Lightbulb className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                    {area}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No improvement areas identified yet</p>
            )}
          </div>
        </div>

        {/* Behavioral Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Positive Behaviors */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <ThumbsUp className="w-5 h-5 text-green-400" />
              Positive Behaviors
            </h2>
            {data.positive_behaviors && data.positive_behaviors.length > 0 ? (
              <ul className="space-y-2">
                {data.positive_behaviors.map((behavior, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-300">
                    <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                    {behavior}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No positive behaviors noted</p>
            )}
          </div>
          
          {/* Red Flags */}
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              Red Flags & Concerns
            </h2>
            {data.red_flag_behaviors && data.red_flag_behaviors.length > 0 ? (
              <ul className="space-y-2">
                {data.red_flag_behaviors.map((flag, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-300">
                    <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                    {flag}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-green-400/70">No red flags identified ✓</p>
            )}
          </div>
        </div>

        {/* Notable Quotes */}
        {data.notable_quotes && data.notable_quotes.length > 0 && (
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Quote className="w-5 h-5 text-purple-400" />
              Notable Quotes
            </h2>
            <div className="space-y-3">
              {data.notable_quotes.map((quote, i) => (
                <blockquote key={i} className="border-l-2 border-purple-500 pl-4 text-gray-300 italic">
                  "{quote}"
                </blockquote>
              ))}
            </div>
          </div>
        )}

        {/* Follow-up Topics */}
        {data.follow_up_topics && data.follow_up_topics.length > 0 && (
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-400" />
              Suggested Follow-up Topics
            </h2>
            <div className="flex flex-wrap gap-2">
              {data.follow_up_topics.map((topic, i) => (
                <span key={i} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm">
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Recommendation */}
        {data.detailed_recommendation && (
          <div className="bg-black/30 rounded-2xl p-6 border border-purple-500/20">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-purple-400" />
              Detailed Recommendation
            </h2>
            <div className="prose prose-invert max-w-none">
              <p className="text-gray-300 whitespace-pre-wrap">{data.detailed_recommendation}</p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-gray-500 text-sm py-4">
          Analysis generated on {new Date(data.analyzed_at).toLocaleString()}
        </div>
      </div>
    </div>
  )
}

