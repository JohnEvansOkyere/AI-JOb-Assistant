# Environment Variables Setup

## Backend Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# AI Model Configuration
# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Groq (Alternative)
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-70b-versatile

# Google Gemini (Alternative)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# Voice Services
# STT - OpenAI Whisper
WHISPER_API_KEY=your-openai-api-key

# STT - Deepgram (Alternative)
DEEPGRAM_API_KEY=your-deepgram-api-key

# TTS - ElevenLabs
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_VOICE_ID=your-voice-id

# Application
APP_ENV=development
APP_DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Interview Configuration
MAX_INTERVIEW_DURATION_SECONDS=1800
MAX_TOKENS_PER_INTERVIEW=50000
DEFAULT_INTERVIEW_DURATION_SECONDS=1200

# Storage
SUPABASE_STORAGE_BUCKET_CVS=cvs
SUPABASE_STORAGE_BUCKET_AUDIO=interview-audio

# Logging
LOG_LEVEL=INFO
```

## Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory with the following variables:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
# Production: https://your-backend.onrender.com

# Application
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

## Getting API Keys

### Supabase
1. Create account at https://supabase.com
2. Create new project
3. Go to Settings → API
4. Copy URL and anon key
5. Copy service_role key (keep secret!)

### OpenAI
1. Create account at https://platform.openai.com
2. Go to API Keys section
3. Create new secret key

### ElevenLabs
1. Create account at https://elevenlabs.io
2. Go to Profile → API Keys
3. Copy API key
4. Go to Voice Library to get Voice ID

### Deepgram (Optional)
1. Create account at https://deepgram.com
2. Go to API Keys section
3. Create new API key

### Groq (Optional)
1. Create account at https://groq.com
2. Go to API Keys section
3. Create new API key

### Google Gemini (Optional)
1. Create account at https://makersuite.google.com/app/apikey
2. Create new API key

## Security Notes

- **Never commit `.env` or `.env.local` files to git**
- Use different keys for development and production
- Rotate keys regularly
- Use service role key only on backend, never expose to frontend

