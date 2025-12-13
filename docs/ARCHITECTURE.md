# System Architecture

## High-Level Overview

```
┌─────────────────┐         ┌─────────────────┐
│   Recruiter     │         │    Candidate    │
│   (Browser)     │         │   (Browser)     │
└────────┬────────┘         └────────┬────────┘
         │                            │
         │                            │
    ┌────▼────────────────────────────▼────┐
    │         Next.js Frontend             │
    │         (Vercel)                     │
    └────┬────────────────────────────┬────┘
         │                            │
         │                            │
    ┌────▼────────────────────────────▼────┐
    │         FastAPI Backend              │
    │         (Render)                     │
    └────┬────────────────────────────┬────┘
         │                            │
    ┌────▼────┐  ┌────▼────┐  ┌──────▼──────┐
    │Supabase │  │   AI    │  │   Voice     │
    │Database │  │ Models  │  │   APIs      │
    └─────────┘  └─────────┘  └─────────────┘
```

## Component Details

### Frontend (Next.js)

- **Framework**: Next.js 14+ (App Router)
- **UI Library**: React + Tailwind CSS
- **State Management**: React Context / Zustand
- **Real-time**: WebSocket for voice streaming
- **Auth**: Supabase Auth client
- **Deployment**: Vercel

### Backend (FastAPI)

- **Framework**: FastAPI (Python 3.11+)
- **Database**: Supabase PostgreSQL (via Supabase client)
- **Real-time**: WebSocket endpoints
- **File Storage**: Supabase Storage
- **Task Queue**: Background tasks for report generation
- **Deployment**: Render

### AI & Voice Services

- **STT**: OpenAI Whisper API or Deepgram
- **TTS**: ElevenLabs (HR professional voice)
- **AI Model**: Multi-modal (Grok/Gemini/Groq/OpenAI)
  - Cost-optimized: GPT-4o-mini or equivalent
  - Token limits enforced per interview

## Data Flow

### Interview Flow

1. **Recruiter** creates job description → stored in Supabase
2. **Recruiter** uploads candidate CV → parsed and stored
3. **System** generates interview ticket → one-time code
4. **Candidate** enters ticket → validates and creates interview session
5. **Real-time Voice Interview**:
   - AI speaks question (TTS)
   - Candidate responds (mic → STT)
   - AI processes response
   - AI generates next question
   - Loop until time limit or completion
6. **System** generates report → stored in database
7. **Recruiter** views report on dashboard

### Security Flow

- **Recruiters**: Authenticated via Supabase Auth
- **Candidates**: Access via one-time ticket only
- **RLS Policies**: Database-level access control
- **API Endpoints**: JWT validation
- **Storage**: Bucket-level policies

## Cost Optimization

1. **Token Limits**: Cap tokens per interview (e.g., 50K tokens max)
2. **Streaming**: Use streaming APIs where possible
3. **Caching**: Cache job descriptions and CVs
4. **Model Selection**: Use cheaper models for non-critical operations
5. **Audio Cleanup**: Archive/delete audio after processing
6. **Time Limits**: Enforce 20-30 minute interview cap

## Scalability Considerations

- **Database**: Supabase auto-scaling PostgreSQL
- **Backend**: Render auto-scaling
- **Frontend**: Vercel edge network
- **WebSocket**: Connection pooling
- **File Storage**: Supabase Storage (CDN-backed)

## Monitoring & Logging

- **Error Tracking**: Sentry or similar
- **Analytics**: Custom dashboard metrics
- **Logging**: Structured logging (JSON)
- **Performance**: APM for API response times

