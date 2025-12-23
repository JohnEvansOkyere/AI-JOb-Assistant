# Testing Guide

## Quick Start

### Run All Tests
```bash
pytest
```

### Run Tests by Category
```bash
# Unit tests only
pytest -m unit

# API endpoint tests
pytest -m api

# Authentication tests (across all modules)
pytest -m auth

# Utility tests
pytest -m utils

# AI provider tests
pytest -m ai

# File upload tests
pytest -m file_upload
```

### Using the Test Runner Script
```bash
# Run unit tests
./run_tests.sh -c unit

# Run API tests with coverage
./run_tests.sh -c api --coverage

# Run auth tests verbosely
./run_tests.sh -c auth -v
```

## Test Categories

### Available Categories

| Category | Marker | Description | Test Count |
|----------|--------|-------------|------------|
| Unit | `-m unit` | Fast, isolated unit tests | ~106 |
| API | `-m api` | API endpoint tests | ~22 |
| Utils | `-m utils` | Utility function tests | ~106 |
| AI | `-m ai` | AI provider tests | ~20 |
| Auth | `-m auth` | Authentication/authorization | ~30 |
| File Upload | `-m file_upload` | File validation tests | ~40 |
| Service | `-m service` | Service layer tests | TBD |
| Integration | `-m integration` | Integration tests | TBD |

### Category Breakdown

#### Unit Tests (`-m unit`)
Fast, isolated tests that don't require external services:
- Utility functions
- Validators
- Helpers
- Pure functions

```bash
pytest -m unit -v
```

#### API Tests (`-m api`)
All API endpoint tests:
- Authentication endpoints
- Job description endpoints
- Application endpoints
- Interview endpoints
- Ticket endpoints

```bash
pytest -m api -v
```

#### Authentication Tests (`-m auth`)
All authentication-related tests across modules:
- Auth utilities (JWT, tokens)
- Auth API endpoints
- Authorization checks

```bash
pytest -m auth -v
```

## Common Test Commands

### Basic Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with extra verbose output
pytest -vv

# Stop on first failure
pytest -x

# Run failed tests only (from last run)
pytest --lf
```

### Category-Specific
```bash
# Run specific category
pytest -m unit
pytest -m api
pytest -m utils

# Combine categories
pytest -m "api or auth"
pytest -m "unit and not slow"

# Exclude categories
pytest -m "not slow"
```

### Coverage
```bash
# Run with coverage (no fail threshold)
pytest --cov=app

# Run with coverage and fail if below 80%
pytest --cov=app --cov-fail-under=80

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Then open: htmlcov/index.html

# Generate coverage for specific category
pytest -m api --cov=app/api --cov-report=term-missing
```

### Debugging
```bash
# Run with print statements visible
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run specific test file
pytest tests/api/test_auth.py

# Run specific test class
pytest tests/api/test_auth.py::TestLogin

# Run specific test function
pytest tests/api/test_auth.py::TestLogin::test_login_success
```

## Running Tests During Development

### Quick Iteration
```bash
# While developing a specific feature
pytest tests/api/test_auth.py -v

# Watch for changes (requires pytest-watch)
ptw tests/api/test_auth.py
```

### Pre-Commit Check
```bash
# Run related category
pytest -m api -v

# Or run changed files
pytest tests/api/ tests/utils/ -v
```

### Full Test Suite
```bash
# All tests with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing
```

## Test Organization

### Directory Structure
```
tests/
├── api/              # API endpoint tests (marker: api)
│   ├── test_auth.py          # Also marked: auth
│   └── test_job_descriptions.py
├── services/         # Service layer tests (marker: service)
├── utils/            # Utility tests (marker: utils)
│   ├── test_auth.py          # Also marked: auth
│   ├── test_input_validation.py
│   ├── test_file_validation.py  # Also marked: file_upload
│   └── ...
└── ai/               # AI provider tests (marker: ai)
    └── test_providers.py
```

### Test Markers
Tests use markers for categorization:

```python
@pytest.mark.unit
@pytest.mark.api
@pytest.mark.auth
@pytest.mark.utils
@pytest.mark.ai
@pytest.mark.file_upload
@pytest.mark.service
@pytest.mark.integration
@pytest.mark.slow
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    pytest -m "not slow" --cov=app --cov-report=xml
    
- name: Run slow tests (optional)
  run: |
    pytest -m slow
```

### Parallel Execution
```bash
# Install pytest-xdist first
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Run specific category in parallel
pytest -m api -n auto
```

## Troubleshooting

### Tests Failing Unexpectedly
```bash
# Run with verbose output to see what's happening
pytest -vv tests/api/test_auth.py

# Check if it's a fixture issue
pytest --setup-show tests/api/test_auth.py
```

### Coverage Issues
```bash
# Check what's not covered
pytest --cov=app --cov-report=term-missing

# Focus on specific module
pytest --cov=app/api --cov-report=term-missing
```

### Slow Tests
```bash
# Identify slow tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"
```

## Best Practices

1. **Run relevant tests while developing**
   - Focus on the category you're working on
   - Use `-v` for detailed output

2. **Run full suite before committing**
   - Catch integration issues early
   - Verify no regressions

3. **Use markers effectively**
   - Mark slow tests as `@pytest.mark.slow`
   - Use multiple markers when appropriate

4. **Keep tests fast**
   - Use mocks for external services
   - Avoid real API calls in unit tests

5. **Write descriptive test names**
   - Test names should clearly describe what they test
   - Use `test_<functionality>_<condition>_<expected_result>`

## Additional Resources

- See `TEST_CATEGORIES.md` for detailed category information
- See `TEST_SUMMARY.md` for test coverage summary
- See `README.md` in tests/ for more details

