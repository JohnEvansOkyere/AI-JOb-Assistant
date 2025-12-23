# Test Categories and Running Tests

This document explains how to run tests by category/feature area.

## Test Categories

Tests are organized using pytest markers for easy categorical testing:

### 1. **Unit Tests** (`-m unit`)
Fast, isolated unit tests that don't require external services.

```bash
pytest -m unit
```

**Coverage**: Utility functions, validators, helper functions

### 2. **Integration Tests** (`-m integration`)
Tests that verify integration between components.

```bash
pytest -m integration
```

### 3. **API Tests** (`-m api`)
All API endpoint tests.

```bash
pytest -m api
```

**Coverage**: 
- Authentication endpoints (`/auth/*`)
- Job descriptions (`/job-descriptions/*`)
- Applications (`/applications/*`)
- CV uploads (`/cvs/*`)
- Interviews (`/interviews/*`)
- Tickets (`/tickets/*`)
- And more...

### 4. **Authentication Tests** (`-m auth`)
All authentication and authorization related tests.

```bash
pytest -m auth
```

**Coverage**:
- Authentication utilities (JWT, tokens)
- Auth API endpoints (register, login, logout)
- Authorization checks

### 5. **Service Tests** (`-m service`)
Service layer business logic tests.

```bash
pytest -m service
```

**Coverage**:
- CV parser service
- CV screening service
- Interview service
- Ticket service
- Email service
- Job description service

### 6. **AI Provider Tests** (`-m ai`)
AI provider and model integration tests.

```bash
pytest -m ai
```

**Coverage**:
- AI provider factory
- OpenAI, Groq, Gemini, Grok providers
- Fallback logic
- Token counting

### 7. **File Upload Tests** (`-m file_upload`)
File upload and validation tests.

```bash
pytest -m file_upload
```

**Coverage**:
- File validation
- File type checking
- File size validation
- Filename sanitization

### 8. **Utility Tests** (`-m utils`)
Utility function tests.

```bash
pytest -m utils
```

**Coverage**:
- Input validation
- Error handling
- Rate limiting
- Auth utilities

## Running Tests by Category

### Single Category
```bash
# Run only API tests
pytest -m api

# Run only authentication tests
pytest -m auth

# Run only utility tests
pytest -m utils
```

### Multiple Categories
```bash
# Run both API and auth tests
pytest -m "api or auth"

# Run unit tests but exclude slow tests
pytest -m "unit and not slow"

# Run API and service tests
pytest -m "api or service"
```

### By Test File/Directory
```bash
# Run all tests in a specific directory
pytest tests/api/
pytest tests/utils/
pytest tests/ai/

# Run a specific test file
pytest tests/api/test_auth.py
pytest tests/utils/test_input_validation.py
```

### By Test Class or Function
```bash
# Run a specific test class
pytest tests/api/test_auth.py::TestLogin

# Run a specific test function
pytest tests/api/test_auth.py::TestLogin::test_login_success
```

## Common Test Run Patterns

### Quick Development Testing
```bash
# Run only unit tests (fastest)
pytest -m unit -v

# Run a specific category while developing
pytest -m api -v --tb=short
```

### Pre-Commit Testing
```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run tests for changed files (if using pytest-watch or similar)
pytest tests/api/ tests/utils/  # Run API and utils tests
```

### CI/CD Pipeline
```bash
# Full test suite with coverage report
pytest --cov=app --cov-report=xml --cov-report=html --junitxml=test-results.xml

# Run by category in parallel (if using pytest-xdist)
pytest -m api -n auto  # Run API tests in parallel
```

### Debugging Failed Tests
```bash
# Run with verbose output and stop on first failure
pytest -xvs tests/api/test_auth.py

# Run with print statements visible
pytest -s tests/api/test_auth.py

# Run and drop into debugger on failure
pytest --pdb tests/api/test_auth.py
```

## Test Organization Structure

```
tests/
├── api/              # API endpoint tests (marker: api)
│   ├── test_auth.py         # Auth endpoints (marker: auth)
│   ├── test_job_descriptions.py  # Job endpoints (marker: api)
│   └── ...
├── services/         # Service layer tests (marker: service)
│   └── ...
├── utils/            # Utility tests (marker: utils)
│   ├── test_auth.py         # Auth utils (marker: auth, utils)
│   ├── test_input_validation.py  # Validation (marker: utils)
│   ├── test_file_validation.py   # File validation (marker: utils, file_upload)
│   └── ...
└── ai/               # AI provider tests (marker: ai)
    └── test_providers.py    # Providers (marker: ai)
```

## Recommended Test Run Workflow

### During Development
1. **Start**: Run specific test file you're working on
   ```bash
   pytest tests/api/test_auth.py -v
   ```

2. **Before Commit**: Run related category
   ```bash
   pytest -m api -v
   ```

3. **Before Push**: Run all tests
   ```bash
   pytest --cov=app
   ```

### For Specific Features

**Working on Authentication?**
```bash
pytest -m auth -v
```

**Working on File Uploads?**
```bash
pytest -m file_upload -v
```

**Working on AI Integration?**
```bash
pytest -m ai -v
```

**Working on API Endpoints?**
```bash
pytest -m api -v
```

## Coverage by Category

Run coverage for specific categories:

```bash
# Coverage for API tests only
pytest -m api --cov=app/api --cov-report=term-missing

# Coverage for utilities only
pytest -m utils --cov=app/utils --cov-report=term-missing

# Coverage for AI providers
pytest -m ai --cov=app/ai --cov-report=term-missing
```

## Tips

1. **Use `-v` for verbose output** to see which tests are running
2. **Use `-k` for keyword filtering** if markers aren't enough:
   ```bash
   pytest -k "login"  # Run all tests with "login" in name
   ```
3. **Combine markers and keywords**:
   ```bash
   pytest -m api -k "job"  # API tests with "job" in name
   ```
4. **Use `--tb=short`** for shorter tracebacks
5. **Use `--lf` (last failed)** to rerun only failed tests from last run

