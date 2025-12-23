"""
Tests for authentication utilities
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from jose import JWTError, jwt
from fastapi import HTTPException, status
from unittest.mock import patch, MagicMock

from app.utils.auth import (
    create_access_token,
    get_current_user,
    get_current_user_id,
    verify_supabase_token
)
from app.config import settings


@pytest.mark.unit
@pytest.mark.utils
class TestCreateAccessToken:
    """Tests for create_access_token function"""
    
    def test_create_token_with_default_expiry(self):
        """Test token creation with default expiry"""
        data = {"sub": str(uuid4()), "email": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
        assert "exp" in payload
    
    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiry"""
        data = {"sub": str(uuid4())}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Should expire in approximately 2 hours
        assert (exp_time - now).total_seconds() > 7000  # ~2 hours
        assert (exp_time - now).total_seconds() < 7300  # ~2 hours + small buffer
    
    def test_token_expires_after_time(self):
        """Test that token expires after specified time"""
        data = {"sub": str(uuid4())}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expires_delta)
        
        with pytest.raises(JWTError):
            jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    
    def test_token_contains_all_data(self):
        """Test that token contains all provided data"""
        data = {
            "sub": str(uuid4()),
            "email": "test@example.com",
            "role": "recruiter",
            "custom_field": "custom_value"
        }
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
        assert payload["role"] == data["role"]
        assert payload["custom_field"] == data["custom_field"]


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.asyncio
class TestGetCurrentUser:
    """Tests for get_current_user function"""
    
    async def test_valid_token_returns_user(self, mock_supabase_client, test_user):
        """Test that valid token returns user data"""
        user_id = test_user["id"]
        token = create_access_token({"sub": user_id})
        
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Mock database response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        with patch('app.utils.auth.db.client', mock_supabase_client):
            user = await get_current_user(credentials)
            assert user == test_user
            assert user["id"] == user_id
    
    async def test_invalid_token_raises_exception(self):
        """Test that invalid token raises HTTPException"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "WWW-Authenticate" in exc_info.value.headers
    
    async def test_expired_token_raises_exception(self):
        """Test that expired token raises HTTPException"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        data = {"sub": str(uuid4())}
        expires_delta = timedelta(seconds=-1)
        expired_token = create_access_token(data, expires_delta=expires_delta)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_token_without_sub_raises_exception(self):
        """Test that token without 'sub' raises HTTPException"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        data = {"email": "test@example.com"}  # No 'sub' field
        token = create_access_token(data)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_user_not_found_raises_exception(self, mock_supabase_client):
        """Test that non-existent user raises HTTPException"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        user_id = str(uuid4())
        token = create_access_token({"sub": user_id})
        
        # Mock empty database response
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with patch('app.utils.auth.db.client', mock_supabase_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_database_error_raises_exception(self, mock_supabase_client):
        """Test that database error raises HTTPException"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        user_id = str(uuid4())
        token = create_access_token({"sub": user_id})
        
        # Mock database error
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with patch('app.utils.auth.db.client', mock_supabase_client):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.asyncio
class TestGetCurrentUserId:
    """Tests for get_current_user_id function"""
    
    async def test_returns_uuid_from_user(self, test_user, test_user_id):
        """Test that function returns UUID from user dict"""
        from app.utils.auth import get_current_user_id
        
        result = await get_current_user_id(test_user)
        assert result == test_user_id
        assert isinstance(result, uuid4().__class__)
    
    async def test_handles_string_uuid(self):
        """Test that function handles string UUID correctly"""
        from app.utils.auth import get_current_user_id
        from uuid import UUID
        
        user_id_str = str(uuid4())
        user = {"id": user_id_str}
        
        result = await get_current_user_id(user)
        assert result == UUID(user_id_str)


@pytest.mark.unit
@pytest.mark.utils
class TestVerifySupabaseToken:
    """Tests for verify_supabase_token function"""
    
    def test_returns_none(self):
        """Test that function returns None (placeholder implementation)"""
        result = verify_supabase_token("test_token")
        assert result is None

