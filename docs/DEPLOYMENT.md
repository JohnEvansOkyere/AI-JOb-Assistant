# Deployment Guide

## Backend Deployment (Render)

### Prerequisites

1. Render account
2. GitHub repository connected
3. Environment variables configured

### Steps

1. **Create Web Service**
   - New → Web Service
   - Connect GitHub repository
   - Select branch (main/production)

2. **Configure Build**
   ```bash
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables**
   - Add all variables from `.env.example`
   - Use Render's environment variable interface

4. **Deploy**
   - Render auto-deploys on push
   - Monitor logs for errors

### Health Check

- Endpoint: `/health`
- Render will use this for health checks

## Frontend Deployment (Vercel)

### Prerequisites

1. Vercel account
2. GitHub repository connected

### Steps

1. **Import Project**
   - New Project → Import from GitHub
   - Select repository and branch

2. **Configure**
   - Framework Preset: Next.js
   - Root Directory: `frontend/`
   - Build Command: `npm run build` (or `yarn build`)
   - Output Directory: `.next`

3. **Environment Variables**
   - Add all `NEXT_PUBLIC_*` variables
   - Add backend API URL

4. **Deploy**
   - Vercel auto-deploys on push
   - Preview deployments for PRs

## Supabase Setup

### Database

1. Create new Supabase project
2. Run `database/schema.sql` in SQL Editor
3. Verify tables and RLS policies

### Storage Buckets

1. Create buckets:
   - `cvs` (public read, authenticated write)
   - `interview-audio` (authenticated read/write)
   - `response-audio` (optional, authenticated read/write)

2. Configure policies:
   - Recruiters can upload CVs
   - System can store interview audio
   - Recruiters can read their job's data

### Authentication

1. Enable Email/Password auth
2. Configure email templates (optional)
3. Set up OAuth providers if needed

## Post-Deployment Checklist

- [ ] Database migrations applied
- [ ] Storage buckets created
- [ ] RLS policies tested
- [ ] Environment variables set
- [ ] Health checks passing
- [ ] CORS configured correctly
- [ ] API endpoints accessible
- [ ] Frontend connects to backend
- [ ] Authentication working
- [ ] File uploads working
- [ ] WebSocket connections working

## Monitoring

- **Backend**: Render logs + error tracking
- **Frontend**: Vercel analytics + error tracking
- **Database**: Supabase dashboard
- **Costs**: Monitor API usage (OpenAI, ElevenLabs, etc.)

## Rollback Procedure

### Backend
- Render: Previous deployment → Promote

### Frontend
- Vercel: Deployments → Select previous → Promote

### Database
- Supabase: Use migrations to rollback
- Or restore from backup

