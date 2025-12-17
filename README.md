# AI-Powered Voice Interview Platform

A production-ready, cost-optimized platform for conducting real-time AI-powered voice interviews based on job descriptions and candidate CVs.

## Architecture

- **Backend**: FastAPI (Python) - Deployed on Render
- **Frontend**: Next.js (React) - Deployed on Vercel
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **Voice**: OpenAI Whisper/Deepgram (STT) + ElevenLabs (TTS)
- **AI Model**: Multi-modal (Grok/Gemini/Groq/OpenAI - cost-optimized)

## Project Structure

```
AI-JOb-Assistant/
├── backend/              # FastAPI application
├── frontend/             # Next.js application
├── database/             # Supabase migrations and schema
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Development Phases

1. ✅ **Phase 1: Project Setup & Database Schema**
   - Initialize project structure
   - Set up Supabase database schema
   - Configure environment variables

2. ✅ **Phase 2: Backend Foundation**
   - FastAPI project structure
   - Database models (Pydantic)
   - Authentication setup (JWT + Supabase Auth)

3. ✅ **Phase 3: Core Backend Features**
   - Job description CRUD
   - CV upload and parsing
   - Interview ticket system

4. ✅ **Phase 4: AI Integration**
   - Multi-provider AI support (OpenAI, Groq, Gemini)
   - Prompt templates
   - Question generation
   - Token tracking and cost optimization

5. ⏳ **Phase 5: Voice Pipeline**
   - STT integration (Whisper/Deepgram)
   - TTS integration (ElevenLabs)
   - WebSocket streaming

6. ⏳ **Phase 6: Interview Logic & Scoring**
   - Interview flow orchestration
   - Adaptive question generation
   - Response scoring and reports

7. ✅ **Phase 7: Frontend Foundation**
   - Next.js setup
   - Supabase client integration
   - Authentication UI
   - Basic dashboard structure

8. ✅ **Phase 8: Job Application Flow**
   - Public job application form (LinkedIn-style)
   - CV screening system with AI matching
   - Application management dashboard
   - Batch screening capabilities
   - Interview ticket generation from qualified candidates

9. ✅ **Phase 11: Candidate Ranking & Enhanced Review**
   - Candidate details page
   - Enhanced application review with AI analysis display
   - Rankings dashboard for all jobs
   - Job-specific ranked candidate lists
   - Direct ticket issuance from ranking views

10. ✅ **Phase 12: Email System & Calendar Integration**
    - Email service with Resend integration
    - Company branding/letterhead management
    - Email templates and history tracking
    - Calendar event management
    - Automatic ticket email delivery
    - See [Email System Phase Documentation](./docs/EMAIL_SYSTEM_PHASE.md)

11. ⏳ **Phase 9: Frontend Features**
    - Enhanced recruiter dashboard
    - Interview UI for candidates
    - Report viewing and analytics
    - Email composer UI
    - Branding manager UI
    - Calendar view

12. ⏳ **Phase 10: Security & Polish**
    - Enhanced access control
    - Comprehensive error handling
    - Deployment configurations
    - Performance optimization

## Getting Started


## Features

### Core Features
- Real-time voice interviews (planned)
- AI-powered question generation
- Multi-modal AI support (OpenAI, Groq, Gemini)
- Cost-optimized token tracking
- Structured interview reports (planned)

### Application Management
- Public job application form (no authentication required)
- AI-powered CV screening and matching
- Batch application screening
- Match scoring (0-100) with detailed breakdowns
- Application status tracking
- Interview ticket generation from qualified candidates

### Email & Communication
- Custom email composer with company branding
- Company letterhead/logo management
- Automatic interview ticket email delivery
- Email templates and history tracking
- Calendar event management for interviews
- Google Calendar integration (in progress)

### Comprehensive CV Screening (Resume Worded Style)
- **Multi-category scoring**: 9 categories with 20+ criteria
- **Experience analysis**: Action verbs, quantification, accomplishments
- **Skills matching**: Technical/soft skills with job requirement comparison
- **ATS compatibility**: Parsability and keyword optimization
- **Format analysis**: Consistency, template, fonts, page length
- **Structure analysis**: Section organization, contact info
- **Language analysis**: Grammar, tense, pronouns, filler words
- **Impact analysis**: Brevity, clarity, professionalism
- **Visual dashboard**: Animated score bars and circles
- **Strengths & issues**: Actionable improvement suggestions


## Environment Variables

See `.env.example` files in backend/ and frontend/ directories.
