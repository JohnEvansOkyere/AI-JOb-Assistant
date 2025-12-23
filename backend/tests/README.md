# Backend Test Suite

Comprehensive production-level test suite for the AI Job Assistant backend.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── api/                     # API endpoint tests
│   ├── test_auth.py
│   ├── test_job_descriptions.py
│   └── ...
├── services/                # Service layer tests
├── utils/                   # Utility function tests
│   ├── test_auth.py
│   ├── test_input_validation.py
│   ├── test_file_validation.py
│   ├── test_errors.py
│   └── test_rate_limit.py
├── ai/                      # AI provider tests
│   └── test_providers.py
└── models/                  # Model validation tests
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/api/test_auth.py
```

### Run specific test class
```bash
pytest tests/api/test_auth.py::TestLogin
```

### Run specific test
```bash
pytest tests/api/test_auth.py::TestLogin::test_login_success
```

### Run tests by marker
```bash
pytest -m unit              # Run unit tests only
pytest -m integration       # Run integration tests only
pytest -m api               # Run API tests only
pytest -m auth              # Run auth-related tests
```

### Run tests in verbose mode
```bash
pytest -v
```

### Run tests with output
```bash
pytest -s
```

## Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests (may require external services)
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.utils` - Utility function tests
- `@pytest.mark.ai` - AI provider tests
- `@pytest.mark.auth` - Authentication/authorization tests
- `@pytest.mark.file_upload` - File upload tests
- `@pytest.mark.slow` - Slow tests (may be skipped in CI)

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `client` - FastAPI test client
- `async_client` - Async test client
- `mock_supabase_client` - Mocked Supabase client
- `test_user` - Sample user data
- `test_user_id` - Sample user ID
- `auth_token` - Valid JWT token
- `auth_headers` - Authorization headers
- `sample_pdf_file` - Mock PDF file
- `sample_docx_file` - Mock DOCX file
- `sample_txt_file` - Mock TXT file
- `mock_ai_provider` - Mock AI provider

## Coverage Goals

- **Overall Coverage**: 80%+ (configured in pytest.ini)
- **Critical Paths**: 90%+ (auth, AI providers, file processing)
- **API Endpoints**: 85%+ (all major endpoints)
- **Services**: 80%+ (business logic)
- **Utils**: 90%+ (validation, helpers)

## Writing New Tests

1. **Follow the existing structure** - Place tests in appropriate directories
2. **Use fixtures** - Leverage existing fixtures from `conftest.py`
3. **Add markers** - Use appropriate pytest markers
4. **Test both success and failure cases** - Cover edge cases and error handling
5. **Mock external dependencies** - Use mocks for Supabase, AI APIs, etc.
6. **Use descriptive names** - Test names should clearly describe what they test

### Example Test

```python
@pytest.mark.api
@pytest.mark.auth
class TestLogin:
    """Tests for POST /auth/login endpoint"""
    
    def test_login_success(self, client, mock_supabase_client):
        """Test successful login"""
        # Setup mocks
        mock_auth_response = MagicMock()
        mock_auth_response.user = MagicMock(id=str(uuid4()))
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        
        # Make request
        with patch('app.database.db.client', mock_supabase_client):
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()["data"]
```

## Continuous Integration

Tests should be run in CI/CD pipeline:

1. Run all tests
2. Check coverage meets threshold (80%)
3. Fail build if tests fail or coverage drops below threshold

## Notes

- All external services (Supabase, AI APIs) are mocked
- Tests use in-memory database/client mocks
- No real API calls are made during testing
- Test environment variables are set in `conftest.py`

