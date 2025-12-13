/**
 * TypeScript Types
 * Shared type definitions
 */

export interface User {
  id: string
  email: string
  full_name?: string
  company_name?: string
  created_at?: string
  updated_at?: string
}

export interface JobDescription {
  id: string
  recruiter_id: string
  title: string
  description: string
  requirements?: string
  location?: string
  employment_type?: string
  experience_level?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Candidate {
  id: string
  email: string
  full_name?: string
  phone?: string
  created_at: string
  updated_at: string
}

export interface CV {
  id: string
  candidate_id: string
  job_description_id?: string
  file_name: string
  file_path: string
  file_size?: number
  mime_type?: string
  parsed_text?: string
  parsed_json?: Record<string, any>
  uploaded_at: string
}

export interface InterviewTicket {
  id: string
  candidate_id: string
  job_description_id: string
  ticket_code: string
  is_used: boolean
  is_expired: boolean
  used_at?: string
  expires_at?: string
  created_at: string
  created_by?: string
}

export interface Interview {
  id: string
  candidate_id: string
  job_description_id: string
  ticket_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  audio_file_path?: string
  transcript?: string
  created_at: string
}

export interface InterviewReport {
  id: string
  interview_id: string
  skill_match_score?: number
  experience_level?: string
  strengths?: string[]
  weaknesses?: string[]
  red_flags?: string[]
  hiring_recommendation?: string
  recommendation_justification?: string
  full_report?: Record<string, any>
  recruiter_notes?: string
  created_at: string
  updated_at: string
}

