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
├── docs/                 # Documentation (organized by category)
│   ├── voice-interview/  # Voice interview features
│   ├── cv-screening/     # CV screening system
│   ├── subscription-payment/ # Subscriptions & payments
│   ├── email/            # Email system
│   ├── admin/            # Admin dashboard
│   ├── phases-implementation/ # Development phases
│   ├── setup-config/     # Setup & configuration
│   ├── architecture/     # System architecture
│   ├── troubleshooting/   # Error solutions
│   ├── testing/          # Testing guides
│   └── business/         # Business docs
└── scripts/              # Utility scripts
```

## Documentation

📚 **Comprehensive documentation is available in the [`docs/`](./docs/) directory.**

- **[Documentation Index](./docs/README.md)** - Main documentation overview
- **[Quick Reference](./docs/QUICK_REFERENCE.md)** - Common tasks and quick links
- **[Architecture](./docs/architecture/ARCHITECTURE.md)** - System architecture
- **[Setup Guide](./docs/setup-config/ENV_SETUP.md)** - Environment setup
- **[Deployment Guide](./docs/setup-config/DEPLOYMENT.md)** - Deployment instructions

All documentation is organized by category for easy navigation.

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

12. ✅ **Phase 10: Security & Polish** (Partially Complete)
    - ✅ Comprehensive error handling (frontend & backend)
    - ✅ File upload security (size limits, type validation, sanitization)
    - ✅ Environment variable validation
    - ✅ Security headers middleware
    - ✅ Input validation & sanitization
    - ✅ Enhanced health checks
    - ✅ Frontend retry logic with exponential backoff
    - ✅ User-friendly error messages
    - ⏳ Enhanced access control
    - ⏳ Performance optimization

#
## Environment Variables

