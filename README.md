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

1. ✅ Phase 1: Project Setup & Database Schema
2. ⏳ Phase 2: Backend Foundation
3. ⏳ Phase 3: Core Backend Features
4. ⏳ Phase 4: AI Integration
5. ⏳ Phase 5: Voice Pipeline
6. ⏳ Phase 6: Interview Logic & Scoring
7. ⏳ Phase 7: Frontend Foundation
8. ⏳ Phase 8: Frontend Features
9. ⏳ Phase 9: Security & Polish

## Getting Started

See individual phase documentation in `docs/` directory.

## Environment Variables

See `.env.example` files in backend/ and frontend/ directories.
