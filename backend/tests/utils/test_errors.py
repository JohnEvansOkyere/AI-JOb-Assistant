"""
Tests for error handling utilities
"""

import pytest
from fastapi import Request, status
from unittest.mock import MagicMock

from app.utils.errors import (
    AppException,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    AppValidationError,
    app_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


@pytest.mark.unit
@pytest.mark.utils
class TestAppException:
    """Tests for AppException class"""
    
    def test_app_exception_creation(self):
        """Test AppException creation with message"""
        exc = AppException("Test error message")
        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_app_exception_custom_status_code(self):
        """Test AppException with custom status code"""
        exc = AppException("Test error", status_code=status.HTTP_404_NOT_FOUND)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
    
    def test_app_exception_inheritance(self):
        """Test that AppException inherits from Exception"""
        exc = AppException("Test")
        assert isinstance(exc, Exception)


@pytest.mark.unit
@pytest.mark.utils
class TestNotFoundError:
    """Tests for NotFoundError class"""
    
    def test_not_found_error_default_message(self):
        """Test NotFoundError with default message"""
        exc = NotFoundError("User")
        assert "User" in exc.message
        assert "not found" in exc.message
        assert exc.status_code == status.HTTP_404_NOT_FOUND
    
    def test_not_found_error_with_identifier(self):
        """Test NotFoundError with identifier"""
        exc = NotFoundError("User", identifier="123")
        assert "User" in exc.message
        assert "123" in exc.message
        assert exc.status_code == status.HTTP_404_NOT_FOUND
    
    def test_not_found_error_inheritance(self):
        """Test that NotFoundError inherits from AppException"""
        exc = NotFoundError("User")
        assert isinstance(exc, AppException)


@pytest.mark.unit
@pytest.mark.utils
class TestUnauthorizedError:
    """Tests for UnauthorizedError class"""
    
    def test_unauthorized_error_default_message(self):
        """Test UnauthorizedError with default message"""
        exc = UnauthorizedError()
        assert exc.message == "Unauthorized"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_unauthorized_error_custom_message(self):
        """Test UnauthorizedError with custom message"""
        exc = UnauthorizedError("Custom unauthorized message")
        assert exc.message == "Custom unauthorized message"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
@pytest.mark.utils
class TestForbiddenError:
    """Tests for ForbiddenError class"""
    
    def test_forbidden_error_default_message(self):
        """Test ForbiddenError with default message"""
        exc = ForbiddenError()
        assert exc.message == "Forbidden"
        assert exc.status_code == status.HTTP_403_FORBIDDEN
    
    def test_forbidden_error_custom_message(self):
        """Test ForbiddenError with custom message"""
        exc = ForbiddenError("Custom forbidden message")
        assert exc.message == "Custom forbidden message"
        assert exc.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.unit
@pytest.mark.utils
class TestAppValidationError:
    """Tests for AppValidationError class"""
    
    def test_app_validation_error_default_message(self):
        """Test AppValidationError with default message"""
        exc = AppValidationError()
        assert exc.message == "Validation error"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_app_validation_error_custom_message(self):
        """Test AppValidationError with custom message"""
        exc = AppValidationError("Custom validation message")
        assert exc.message == "Custom validation message"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.asyncio
class TestAppExceptionHandler:
    """Tests for app_exception_handler function"""
    
    async def test_handles_app_exception(self):
        """Test that AppException is handled correctly"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        
        exc = AppException("Test error", status_code=status.HTTP_400_BAD_REQUEST)
        response = await app_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        content = response.body.decode()
        assert "success" in content
        assert "false" in content.lower()
        assert "Test error" in content
    
    async def test_handles_not_found_error(self):
        """Test that NotFoundError is handled correctly"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        
        exc = NotFoundError("User", identifier="123")
        response = await app_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        content = response.body.decode()
        assert "User" in content


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.asyncio
class TestValidationExceptionHandler:
    """Tests for validation_exception_handler function"""
    
    async def test_handles_validation_error(self):
        """Test that RequestValidationError is handled correctly"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        
        errors = [{"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"}]
        exc = RequestValidationError(errors=errors)
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        content = response.body.decode()
        assert "validation error" in content.lower()
        assert "details" in content.lower()


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.asyncio
class TestGeneralExceptionHandler:
    """Tests for general_exception_handler function"""
    
    async def test_handles_general_exception(self):
        """Test that general Exception is handled correctly"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        
        exc = Exception("Unexpected error")
        response = await general_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        content = response.body.decode()
        assert "internal server error" in content.lower()
        assert "success" in content
        assert "false" in content.lower()
    
    async def test_handles_unexpected_error(self):
        """Test that unexpected errors are handled gracefully"""
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        
        exc = ValueError("Value error")
        response = await general_exception_handler(request, exc)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

