"""
Pytest configuration and shared fixtures
Provides mocks and test utilities for all tests
"""

import pytest
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from jose import jwt

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment variables before importing app modules
os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-purposes-only"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-supabase-key"
os.environ["SUPABASE_SERVICE_KEY"] = "test-supabase-service-key"

# Import after setting env vars
from app.main import app
from app.config import settings
from app.database import db
import structlog

# Configure test logging
structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(30),  # WARN level
)


# ============================================================================
# Mock Supabase Client Fixtures
# ============================================================================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    mock_client = MagicMock()
    
    # Mock table() method to return a chainable mock
    mock_table = MagicMock()
    mock_query = MagicMock()
    mock_execute = MagicMock()
    
    # Default execute response
    mock_execute.data = []
    mock_execute.execute.return_value = mock_execute
    mock_query.execute.return_value = mock_execute
    mock_table.select.return_value = mock_query
    mock_table.insert.return_value = mock_query
    mock_table.update.return_value = mock_query
    mock_table.delete.return_value = mock_query
    mock_table.upsert.return_value = mock_query
    mock_table.eq.return_value = mock_query
    mock_table.neq.return_value = mock_query
    mock_table.gt.return_value = mock_query
    mock_table.gte.return_value = mock_query
    mock_table.lt.return_value = mock_query
    mock_table.lte.return_value = mock_query
    mock_table.limit.return_value = mock_query
    mock_table.offset.return_value = mock_query
    mock_table.order.return_value = mock_query
    
    mock_client.table.return_value = mock_table
    
    # Mock storage
    mock_storage = MagicMock()
    mock_bucket = MagicMock()
    mock_file = MagicMock()
    
    mock_file.download.return_value = b"test file content"
    mock_file.upload.return_value = {"path": "test/path/file.pdf"}
    mock_file.remove.return_value = {"message": "File removed"}
    mock_file.get_public_url.return_value = "https://test.supabase.co/storage/v1/object/public/test/file.pdf"
    
    mock_bucket.upload.return_value = mock_file
    mock_bucket.download.return_value = b"test file content"
    mock_bucket.remove.return_value = {"message": "File removed"}
    mock_bucket.get_public_url.return_value = "https://test.supabase.co/storage/v1/object/public/test/file.pdf"
    
    mock_storage.from_.return_value = mock_bucket
    mock_client.storage = mock_storage
    
    return mock_client


@pytest.fixture
def mock_supabase_service_client():
    """Mock Supabase service client (bypasses RLS)"""
    return MagicMock()


@pytest.fixture(autouse=True)
def mock_database(mock_supabase_client, mock_supabase_service_client):
    """Mock database instance"""
    with patch.object(db, 'client', mock_supabase_client):
        with patch.object(db, 'service_client', mock_supabase_service_client):
            with patch.object(db, 'get_client') as mock_get_client:
                def get_client_side_effect(use_service_key=False):
                    if use_service_key:
                        return mock_supabase_service_client
                    return mock_supabase_client
                mock_get_client.side_effect = get_client_side_effect
                yield db


# ============================================================================
# Test Client Fixture
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async FastAPI test client (for async endpoints)"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user_id() -> UUID:
    """Generate a test user ID"""
    return uuid4()


@pytest.fixture
def test_user(test_user_id: UUID) -> dict:
    """Create a test user dictionary"""
    return {
        "id": str(test_user_id),
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "recruiter",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def auth_token(test_user_id: UUID) -> str:
    """Generate a valid JWT token for testing"""
    from datetime import timedelta
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": str(test_user_id),
        "exp": expire,
        "email": "test@example.com"
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def mock_get_current_user(test_user: dict):
    """Mock get_current_user dependency"""
    async def _mock_get_current_user():
        return test_user
    return _mock_get_current_user


@pytest.fixture
def mock_get_current_user_id(test_user_id: UUID):
    """Mock get_current_user_id dependency"""
    async def _mock_get_current_user_id():
        return test_user_id
    return _mock_get_current_user_id


# ============================================================================
# AI Provider Fixtures
# ============================================================================

@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for testing"""
    mock_provider = AsyncMock()
    mock_provider.generate_completion = AsyncMock(return_value="Test AI response")
    mock_provider.generate_streaming = AsyncMock()
    mock_provider.get_token_count = Mock(return_value=100)
    mock_provider.model = "test-model"
    
    # Mock streaming generator
    async def mock_stream():
        chunks = ["Test", " AI", " response"]
        for chunk in chunks:
            yield chunk
    mock_provider.generate_streaming.return_value = mock_stream()
    
    return mock_provider


@pytest.fixture
def mock_openai_provider(mock_ai_provider):
    """Mock OpenAI provider"""
    mock_ai_provider.model = settings.openai_model
    return mock_ai_provider


@pytest.fixture
def mock_groq_provider(mock_ai_provider):
    """Mock Groq provider"""
    mock_ai_provider.model = settings.groq_model
    return mock_ai_provider


@pytest.fixture
def mock_gemini_provider(mock_ai_provider):
    """Mock Gemini provider"""
    mock_ai_provider.model = settings.gemini_model
    return mock_ai_provider


@pytest.fixture
def mock_grok_provider(mock_ai_provider):
    """Mock Grok provider"""
    mock_ai_provider.model = settings.grok_model
    return mock_ai_provider


# ============================================================================
# File Upload Fixtures
# ============================================================================

@pytest.fixture
def sample_pdf_content() -> bytes:
    """Generate sample PDF content for testing"""
    # Minimal valid PDF header
    return b"%PDF-1.4\n%test\n"


@pytest.fixture
def sample_pdf_file(sample_pdf_content: bytes):
    """Create a mock PDF file for testing"""
    from fastapi import UploadFile
    from io import BytesIO
    
    file = UploadFile(
        filename="test_cv.pdf",
        file=BytesIO(sample_pdf_content)
    )
    file.content_type = "application/pdf"
    file.size = len(sample_pdf_content)
    return file


@pytest.fixture
def sample_docx_file():
    """Create a mock DOCX file for testing"""
    from fastapi import UploadFile
    from io import BytesIO
    
    # Minimal DOCX content (ZIP header)
    content = b"PK\x03\x04"
    file = UploadFile(
        filename="test_cv.docx",
        file=BytesIO(content)
    )
    file.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    file.size = len(content)
    return file


@pytest.fixture
def sample_txt_file():
    """Create a mock TXT file for testing"""
    from fastapi import UploadFile
    from io import BytesIO
    
    content = b"Test CV content\nName: John Doe\nEmail: john@example.com"
    file = UploadFile(
        filename="test_cv.txt",
        file=BytesIO(content)
    )
    file.content_type = "text/plain"
    file.size = len(content)
    return file


@pytest.fixture
def sample_image_file():
    """Create a mock image file for testing"""
    from fastapi import UploadFile
    from io import BytesIO
    
    # Minimal PNG header
    content = b"\x89PNG\r\n\x1a\n"
    file = UploadFile(
        filename="test_logo.png",
        file=BytesIO(content)
    )
    file.content_type = "image/png"
    file.size = len(content)
    return file


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_job_description_id() -> UUID:
    """Generate a test job description ID"""
    return uuid4()


@pytest.fixture
def sample_job_description_data(sample_job_description_id: UUID, test_user_id: UUID) -> dict:
    """Create sample job description data"""
    return {
        "id": str(sample_job_description_id),
        "recruiter_id": str(test_user_id),
        "title": "Senior Software Engineer",
        "description": "We are looking for an experienced software engineer...",
        "requirements": "5+ years of Python experience",
        "location": "Remote",
        "salary_range": "$100k-$150k",
        "employment_type": "full-time",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_candidate_id() -> UUID:
    """Generate a test candidate ID"""
    return uuid4()


@pytest.fixture
def sample_candidate_data(sample_candidate_id: UUID) -> dict:
    """Create sample candidate data"""
    return {
        "id": str(sample_candidate_id),
        "email": "candidate@example.com",
        "full_name": "John Doe",
        "phone": "+1234567890",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_application_id() -> UUID:
    """Generate a test application ID"""
    return uuid4()


@pytest.fixture
def sample_application_data(
    sample_application_id: UUID,
    sample_candidate_id: UUID,
    sample_job_description_id: UUID
) -> dict:
    """Create sample job application data"""
    return {
        "id": str(sample_application_id),
        "candidate_id": str(sample_candidate_id),
        "job_description_id": str(sample_job_description_id),
        "cover_letter": "I am interested in this position...",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_ticket_code() -> str:
    """Generate a test ticket code"""
    return "TKT" + uuid4().hex[:12].upper()


@pytest.fixture
def sample_ticket_id() -> UUID:
    """Generate a test ticket ID"""
    return uuid4()


@pytest.fixture
def sample_interview_id() -> UUID:
    """Generate a test interview ID"""
    return uuid4()


@pytest.fixture
def sample_interview_data(
    sample_interview_id: UUID,
    sample_ticket_id: UUID,
    sample_candidate_id: UUID,
    sample_job_description_id: UUID
) -> dict:
    """Create sample interview data"""
    return {
        "id": str(sample_interview_id),
        "ticket_id": str(sample_ticket_id),
        "candidate_id": str(sample_candidate_id),
        "job_description_id": str(sample_job_description_id),
        "status": "started",
        "started_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Time Mocking Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """Freezegun fixture for time mocking"""
    from freezegun import freeze_time
    return freeze_time


# ============================================================================
# Environment Variable Mocking
# ============================================================================

@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings to test defaults before each test"""
    # Settings are already loaded, but we can patch specific values if needed
    yield
    # Settings will be re-loaded on next import


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_request():
    """Mock FastAPI Request object"""
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.url.path = "/test"
    request.method = "GET"
    request.headers = {}
    request.state = MagicMock()
    return request


@pytest.fixture
def mock_background_tasks():
    """Mock FastAPI BackgroundTasks"""
    from fastapi import BackgroundTasks
    return BackgroundTasks()


# ============================================================================
# Database Query Helper Fixtures
# ============================================================================

@pytest.fixture
def mock_db_query_success():
    """Helper to create a successful database query response"""
    def _create_response(data: dict | list):
        mock_response = MagicMock()
        mock_response.data = data if isinstance(data, list) else [data]
        mock_response.execute.return_value = mock_response
        return mock_response
    return _create_response


@pytest.fixture
def mock_db_query_empty():
    """Helper to create an empty database query response"""
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.execute.return_value = mock_response
    return mock_response


@pytest.fixture
def mock_db_query_error():
    """Helper to create a database query error"""
    def _create_error(exception_class, message: str):
        error = exception_class(message)
        mock_response = MagicMock()
        mock_response.execute.side_effect = error
        return error
    return _create_error


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_mocks():
    """Clean up mocks after each test"""
    yield
    # Any cleanup needed can go here

