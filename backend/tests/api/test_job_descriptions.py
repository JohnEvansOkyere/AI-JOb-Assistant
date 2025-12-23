"""
Tests for job descriptions API endpoints
"""

import pytest
from fastapi import status
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime


@pytest.mark.api
class TestCreateJobDescription:
    """Tests for POST /job-descriptions endpoint"""
    
    def test_create_job_success(
        self, 
        client, 
        auth_headers, 
        test_user, 
        test_user_id,
        mock_supabase_client
    ):
        """Test successful job description creation"""
        job_data = {
            "title": "Senior Software Engineer",
            "description": "We are looking for an experienced software engineer...",
            "requirements": "5+ years of Python experience",
            "location": "Remote",
            "salary_range": "$100k-$150k",
            "employment_type": "full-time",
            "is_active": True
        }
        
        job_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        created_job = {
            "id": job_id,
            "recruiter_id": str(test_user_id),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            **job_data
        }
        
        # Mock authentication
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        
        # Create separate mocks for client and service_client
        mock_service_client = MagicMock()
        mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [created_job]
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.database.db.service_client', mock_service_client):
                with patch('app.utils.auth.db.client', mock_supabase_client):
                    response = client.post(
                        "/job-descriptions",
                        json=job_data,
                        headers=auth_headers
                    )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == job_data["title"]
        assert data["data"]["recruiter_id"] == str(test_user_id)
    
    def test_create_job_unauthorized(self, client):
        """Test creating job without authentication"""
        job_data = {
            "title": "Senior Software Engineer",
            "description": "We are looking for...",
        }
        
        response = client.post("/job-descriptions", json=job_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_job_missing_required_fields(self, client, auth_headers, test_user, mock_supabase_client):
        """Test creating job with missing required fields"""
        job_data = {
            "title": "Senior Software Engineer"
            # Missing description
        }
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.utils.auth.db.client', mock_supabase_client):
                response = client.post(
                    "/job-descriptions",
                    json=job_data,
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
class TestListJobDescriptions:
    """Tests for GET /job-descriptions endpoint"""
    
    def test_list_jobs_success(
        self,
        client,
        auth_headers,
        test_user,
        test_user_id,
        mock_supabase_client
    ):
        """Test successful job listing"""
        now = datetime.utcnow().isoformat()
        jobs = [
            {
                "id": str(uuid4()),
                "recruiter_id": str(test_user_id),
                "title": "Job 1",
                "description": "Description 1",
                "requirements": None,
                "location": None,
                "employment_type": None,
                "experience_level": None,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            },
            {
                "id": str(uuid4()),
                "recruiter_id": str(test_user_id),
                "title": "Job 2",
                "description": "Description 2",
                "requirements": None,
                "location": None,
                "employment_type": None,
                "experience_level": None,
                "is_active": False,
                "created_at": now,
                "updated_at": now
            }
        ]
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        
        # Mock service_client for listing - chain: eq().order().limit().offset().execute()
        mock_service_client = MagicMock()
        mock_service_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value.data = jobs
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.database.db.service_client', mock_service_client):
                with patch('app.utils.auth.db.client', mock_supabase_client):
                    response = client.get("/job-descriptions", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_list_jobs_filter_active(
        self,
        client,
        auth_headers,
        test_user,
        test_user_id,
        mock_supabase_client
    ):
        """Test listing only active jobs"""
        now = datetime.utcnow().isoformat()
        active_jobs = [
            {
                "id": str(uuid4()),
                "recruiter_id": str(test_user_id),
                "title": "Active Job",
                "description": "Description",
                "requirements": None,
                "location": None,
                "employment_type": None,
                "experience_level": None,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
        ]
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        mock_service_client = MagicMock()
        mock_service_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = active_jobs
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.database.db.service_client', mock_service_client):
                with patch('app.utils.auth.db.client', mock_supabase_client):
                    response = client.get(
                        "/job-descriptions?is_active=true",
                        headers=auth_headers
                    )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert all(job["is_active"] for job in data["data"])


@pytest.mark.api
class TestGetJobDescription:
    """Tests for GET /job-descriptions/{id} endpoint"""
    
    def test_get_job_success(
        self,
        client,
        auth_headers,
        test_user,
        test_user_id,
        sample_job_description_id,
        mock_supabase_client
    ):
        """Test successful job retrieval"""
        now = datetime.utcnow().isoformat()
        job = {
            "id": str(sample_job_description_id),
            "recruiter_id": str(test_user_id),
            "title": "Senior Software Engineer",
            "description": "We are looking for...",
            "requirements": None,
            "location": None,
            "employment_type": None,
            "experience_level": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        mock_service_client = MagicMock()
        mock_service_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [job]
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.database.db.service_client', mock_service_client):
                with patch('app.utils.auth.db.client', mock_supabase_client):
                    response = client.get(
                        f"/job-descriptions/{sample_job_description_id}",
                        headers=auth_headers
                    )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(sample_job_description_id)
    
    def test_get_job_not_found(
        self,
        client,
        auth_headers,
        test_user,
        sample_job_description_id,
        mock_supabase_client
    ):
        """Test retrieving non-existent job"""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        mock_service_client = MagicMock()
        mock_service_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.database.db.service_client', mock_service_client):
                with patch('app.utils.auth.db.client', mock_supabase_client):
                    response = client.get(
                        f"/job-descriptions/{sample_job_description_id}",
                        headers=auth_headers
                    )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestUpdateJobDescription:
    """Tests for PUT /job-descriptions/{id} endpoint"""
    
    def test_update_job_success(
        self,
        client,
        auth_headers,
        test_user,
        test_user_id,
        sample_job_description_id,
        mock_supabase_client
    ):
        """Test successful job update"""
        now = datetime.utcnow().isoformat()
        existing_job = {
            "id": str(sample_job_description_id),
            "recruiter_id": str(test_user_id),
            "title": "Old Title",
            "description": "Old Description",
            "requirements": None,
            "location": None,
            "employment_type": None,
            "experience_level": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        update_data = {
            "title": "New Title",
            "is_active": False
        }
        
        updated_job = {**existing_job, **update_data}
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        mock_service_client = MagicMock()
        mock_service_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [existing_job]
        mock_service_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [updated_job]
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.database.db.service_client', mock_service_client):
                with patch('app.utils.auth.db.client', mock_supabase_client):
                    response = client.put(
                        f"/job-descriptions/{sample_job_description_id}",
                        json=update_data,
                        headers=auth_headers
                    )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "New Title"
        assert data["data"]["is_active"] is False


@pytest.mark.api
class TestDeleteJobDescription:
    """Tests for DELETE /job-descriptions/{id} endpoint"""
    
    def test_delete_job_success(
        self,
        client,
        auth_headers,
        test_user,
        test_user_id,
        sample_job_description_id,
        mock_supabase_client
    ):
        """Test successful job deletion"""
        job = {
            "id": str(sample_job_description_id),
            "recruiter_id": str(test_user_id),
            "title": "Job to Delete"
        }
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [test_user]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [job]
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = [job]
        
        with patch('app.database.db.client', mock_supabase_client):
            with patch('app.utils.auth.db.client', mock_supabase_client):
                response = client.delete(
                    f"/job-descriptions/{sample_job_description_id}",
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

