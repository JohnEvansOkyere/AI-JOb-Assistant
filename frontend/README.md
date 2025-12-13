# Frontend - Next.js Application

## Overview

Next.js frontend for the AI Voice Interview Platform.

## Project Structure

```
frontend/
├── app/                     # Next.js App Router
│   ├── layout.tsx
│   ├── page.tsx
│   ├── (auth)/             # Auth routes
│   ├── (recruiter)/        # Recruiter dashboard
│   └── (candidate)/        # Candidate interface
├── components/             # React components
├── lib/                    # Utilities and clients
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript types
├── public/                 # Static assets
├── .env.example
└── README.md
```

## Setup

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

3. Run development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

4. Open http://localhost:3000

## Environment Variables

See `.env.example` for required variables.

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (or similar)
- **State**: React Context / Zustand
- **Real-time**: WebSocket client
- **Auth**: Supabase Auth

