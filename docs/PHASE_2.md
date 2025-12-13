# Phase 2: Backend Foundation

## Overview

This phase establishes the core backend infrastructure:
- Database models (Pydantic)
- API schemas (Request/Response)
- Authentication middleware
- Error handling
- Basic API routes

## Completed Tasks

✅ Created Pydantic models for all database tables:
- User (recruiter)
- Candidate
- JobDescription
- CV
- InterviewTicket
- Interview
- InterviewQuestion
- InterviewResponse
- InterviewReport

✅ Created API schemas:
- Authentication schemas (Token, UserLogin, UserRegister)
- Common response schemas (Response, ErrorResponse, PaginatedResponse)

✅ Implemented authentication:
- JWT token creation and validation
- User authentication middleware
- Supabase auth integration

✅ Error handling:
- Custom exception classes
- Exception handlers
- Structured error responses

✅ API routes:
- Authentication routes (/auth/register, /auth/login, /auth/me, /auth/logout)
- Health check routes (/health, /health/db)

## File Structure

```
backend/app/
├── models/              # Pydantic database models
│   ├── user.py
│   ├── candidate.py
│   ├── job_description.py
│   ├── cv.py
│   ├── interview_ticket.py
│   ├── interview.py
│   ├── interview_question.py
│   ├── interview_response.py
│   └── interview_report.py
├── schemas/             # API request/response schemas
│   ├── auth.py
│   └── common.py
├── utils/               # Utility functions
│   ├── auth.py          # Authentication utilities
│   └── errors.py        # Error handling
├── api/                 # API routes
│   ├── auth.py          # Authentication endpoints
│   └── health.py        # Health check endpoints
└── main.py              # Updated with routers and error handlers
```

## Key Features

### Authentication

- JWT-based authentication
- Supabase Auth integration
- Protected routes using dependency injection
- Token expiration (24 hours default)

### Error Handling

- Custom exception classes
- Structured error responses
- Validation error handling
- Global exception handler

### Models

- Type-safe Pydantic models
- Separate Create/Update/Base models
- Automatic validation
- Database field mapping

## API Endpoints

### Authentication

- `POST /auth/register` - Register new recruiter
- `POST /auth/login` - Login and get token
- `GET /auth/me` - Get current user (protected)
- `POST /auth/logout` - Logout (protected)

### Health

- `GET /health` - Basic health check
- `GET /health/db` - Database health check

## Testing

To test the API:

1. Start the server:
```bash
cd backend
uvicorn app.main:app --reload
```

2. Visit http://localhost:8000/docs for interactive API documentation

3. Test endpoints:
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "full_name": "Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## Next Steps

Phase 3 will add:
- Job description CRUD endpoints
- CV upload and parsing
- Ticket generation system
- Interview session management

## Notes

- All models use Pydantic v2 syntax
- Authentication uses Supabase Auth + JWT
- Error responses follow consistent format
- All routes are documented with docstrings

