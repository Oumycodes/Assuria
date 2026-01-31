"""
Integration tests for incident API endpoints.
Requires test database and Redis.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app

# Use test client
client = TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass JWT validation."""
    with patch('app.middleware.auth.get_current_user_id') as mock:
        mock.return_value = "test-user-id"
        yield mock


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('app.database.get_supabase_client') as mock:
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": "test-incident-id",
            "user_id": "test-user-id",
            "status": "pending"
        }]
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_llm():
    """Mock LLM service."""
    with patch('app.services.llm_service.extract_incident_data') as mock:
        mock.return_value = {
            "incident_type": "car_accident",
            "severity": "medium",
            "date": "2024-01-15",
            "location": "123 Main St",
            "people_involved": [],
            "documents_detected": [],
            "confidence": 0.85,
            "needs_human": False
        }
        yield mock


@pytest.fixture
def mock_worker():
    """Mock Celery worker."""
    with patch('app.routes.incidents.process_incident_async') as mock:
        yield mock


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_incident(mock_auth, mock_supabase, mock_llm, mock_worker):
    """Test creating an incident."""
    response = client.post(
        "/incident",
        data={"story_text": "My car was hit in a parking lot"},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "incident_id" in data
    assert data["status"] == "pending"
    assert "extracted_data" in data


def test_create_incident_with_file(mock_auth, mock_supabase, mock_llm, mock_worker):
    """Test creating an incident with file attachment."""
    # Create a dummy file
    files = {
        "files": ("test.jpg", b"fake-image-data", "image/jpeg")
    }
    
    response = client.post(
        "/incident",
        data={"story_text": "Test incident"},
        files=files,
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 201


def test_get_incident(mock_auth, mock_supabase):
    """Test getting an incident."""
    # Mock the select query
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
        "id": "test-incident-id",
        "user_id": "test-user-id",
        "status": "verified",
        "story_text": "encrypted-story",
        "extracted_data": '{"incident_type": "car_accident"}',
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }]
    
    # Mock events query
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    
    response = client.get(
        "/incident/test-incident-id",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-incident-id"


def test_get_incident_not_found(mock_auth, mock_supabase):
    """Test getting non-existent incident."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    
    response = client.get(
        "/incident/nonexistent-id",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 404


def test_create_incident_unauthorized():
    """Test creating incident without authentication."""
    response = client.post(
        "/incident",
        data={"story_text": "Test"}
    )
    
    assert response.status_code == 403  # FastAPI returns 403 for missing auth
