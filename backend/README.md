# Backend - FastAPI Application

## Overview

FastAPI backend for the AI Voice Interview Platform.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── ai/                  # AI integration
│   ├── voice/               # Voice pipeline
│   └── utils/               # Utilities
├── docs/                  # Documentation
│   ├── CORS_TROUBLESHOOTING.md
│   └── CORS_CHECKLIST.md
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. Run development server:
```bash
uvicorn app.main:app --reload
```

## Documentation

### Interview System
- **[Interview Question System](../docs/voice-interview/INTERVIEW_QUESTION_SYSTEM.md)** - Comprehensive guide to the enhanced interview question generation system, gap analysis, and interview flow
- **[Interview Flow Examples](../docs/voice-interview/INTERVIEW_FLOW_EXAMPLES.md)** - Real-world examples of interview flows, follow-up decisions, and time management
- **[Quick Reference Guide](../docs/voice-interview/INTERVIEW_QUICK_REFERENCE.md)** - Quick reference for developers with code examples and common patterns
- **[Interview Report Analysis](../docs/voice-interview/INTERVIEW_REPORT_ANALYSIS.md)** - Analysis of report generation system and improvements
- **[Interview Report Finalization](../docs/voice-interview/INTERVIEW_REPORT_FINALIZATION.md)** - Comprehensive documentation of the report finalization system
- **[Troubleshooting Indentation Errors](../docs/voice-interview/TROUBLESHOOTING_INDENTATION_ERRORS.md)** - Guide for fixing indentation and syntax errors in voice.py
- **[Immediate Next Steps](../docs/voice-interview/IMMEDIATE_NEXT_STEPS.md)** - Action items after implementing report finalization

### Configuration
- [CORS Troubleshooting Guide](./docs/CORS_TROUBLESHOOTING.md) - Detailed guide for CORS errors and solutions
- [CORS Configuration Checklist](./docs/CORS_CHECKLIST.md) - Checklist to prevent CORS issues

### Email Configuration
- **[Email Setup Guide](../docs/EMAIL_SETUP_GUIDE.md)** - Complete guide for setting up Resend email service
- **[Email Automation Reference](../docs/EMAIL_AUTOMATION_REFERENCE.md)** - Reference for all automated emails sent by the platform
- **[Email Configuration Summary](../docs/EMAIL_CONFIGURATION_SUMMARY.md)** - Summary of email configuration changes
- **[Email Verification Implementation](../docs/EMAIL_VERIFICATION_IMPLEMENTATION.md)** - Custom OTP email verification system

For more documentation, see the main [docs](../docs/) directory.
