"""
Tests for authentication API endpoints
"""

import pytest
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.schemas.auth import UserRegister, UserLogin


@pytest.mark.api
@pytest.mark.auth
class TestRegister:
    """Tests for POST /auth/register endpoint"""
    
    def test_register_success(self, client, mock_supabase_client):
        """Test successful user registration"""
        user_id = str(uuid4())
        mock_user = MagicMock()
        mock_user.id = user_id
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        
        # Mock Supabase auth.sign_up
        mock_supabase_client.auth.sign_up.return_value = mock_auth_response
        
        # Mock database insert
        now = datetime.utcnow().isoformat()
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": user_id,
            "email": "test@example.com",
            "full_name": "Test User",
            "company_name": "Test Company",
            "created_at": now,
            "updated_at": now
        }]
        
        register_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
        
        with patch('app.database.db.client', mock_supabase_client):
            response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "test@example.com"
        assert data["data"]["full_name"] == "Test User"
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        register_data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
        
        response = client.post("/auth/register", json=register_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        register_data = {
            "email": "test@example.com"
            # Missing password, full_name, company_name
        }
        
        response = client.post("/auth/register", json=register_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_auth_failure(self, client, mock_supabase_client):
        """Test registration when Supabase auth fails"""
        mock_auth_response = MagicMock()
        mock_auth_response.user = None
        
        mock_supabase_client.auth.sign_up.return_value = mock_auth_response
        
        register_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
        
        with patch('app.database.db.client', mock_supabase_client):
            response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.json()["detail"]
        assert "Failed to create user" in detail or "Registration failed" in detail
    
    def test_register_database_failure(self, client, mock_supabase_client):
        """Test registration when database insert fails"""
        user_id = str(uuid4())
        mock_user = MagicMock()
        mock_user.id = user_id
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        
        mock_supabase_client.auth.sign_up.return_value = mock_auth_response
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = []
        
        register_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
        
        with patch('app.database.db.client', mock_supabase_client):
            response = client.post("/auth/register", json=register_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.json()["detail"]
        assert "Failed to create user profile" in detail or "Registration failed" in detail


@pytest.mark.api
@pytest.mark.auth
class TestLogin:
    """Tests for POST /auth/login endpoint"""
    
    def test_login_success(self, client, mock_supabase_client):
        """Test successful login"""
        user_id = str(uuid4())
        mock_user = MagicMock()
        mock_user.id = user_id
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        with patch('app.database.db.client', mock_supabase_client):
            response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, mock_supabase_client):
        """Test login with invalid credentials"""
        mock_auth_response = MagicMock()
        mock_auth_response.user = None
        
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_auth_response
        
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword"
        }
        
        with patch('app.database.db.client', mock_supabase_client):
            response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        login_data = {
            "email": "test@example.com"
            # Missing password
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_exception_handling(self, client, mock_supabase_client):
        """Test login exception handling"""
        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Auth error")
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        with patch('app.database.db.client', mock_supabase_client):
            response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
@pytest.mark.auth
class TestGetMe:
    """Tests for GET /auth/me endpoint"""
    
    def test_get_me_success(self, client, auth_headers, test_user, mock_supabase_client):
        """Test getting current user information"""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.utils.auth.db.client', mock_supabase_client):
                response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user["email"]
    
    def test_get_me_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.api
@pytest.mark.auth
class TestLogout:
    """Tests for POST /auth/logout endpoint"""
    
    def test_logout_success(self, client, auth_headers, test_user, mock_supabase_client):
        """Test successful logout"""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.utils.auth.db.client', mock_supabase_client):
                response = client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "Logged out successfully" in data["message"]
    
    def test_logout_unauthorized(self, client):
        """Test logout without authentication"""
        response = client.post("/auth/logout")
        assert response.status_code == status.HTTP_403_FORBIDDEN

