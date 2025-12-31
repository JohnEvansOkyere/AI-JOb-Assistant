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

- [CORS Troubleshooting Guide](./docs/CORS_TROUBLESHOOTING.md) - Detailed guide for CORS errors and solutions
- [CORS Configuration Checklist](./docs/CORS_CHECKLIST.md) - Checklist to prevent CORS issues

For more documentation, see the main [docs](../docs/) directory.
