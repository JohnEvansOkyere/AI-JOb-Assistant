# Database Schema

This directory contains Supabase database migrations and schema definitions.

## Files

- `schema.sql` - Complete database schema (tables, indexes, RLS policies)
- `migrations/` - Individual migration files for version control

## Setup

1. Create a Supabase project
2. Run `schema.sql` in the Supabase SQL editor
3. Or apply migrations sequentially from `migrations/` directory

## Schema Overview

### Core Tables

- `users` - Recruiters (extends Supabase auth.users)
- `candidates` - Candidate profiles
- `job_descriptions` - Job postings
- `cvs` - CV files and parsed content
- `interview_tickets` - One-time access tickets
- `interviews` - Interview sessions
- `interview_questions` - Generated questions
- `interview_responses` - Candidate responses
- `interview_reports` - Final evaluation reports

