"""
Pytest configuration and fixtures for testing.
"""

import pytest
import os
from unittest.mock import Mock, patch
from app.config import Settings

# Set test environment
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        supabase_url="https://test.supabase.co",
        supabase_key="test-key",
        supabase_service_role_key="test-service-key",
        supabase_db_url="postgresql://test:test@localhost/test",
        encryption_key="test-encryption-key-32-bytes-long!!",
        anthropic_api_key="test-anthropic-key",
        redis_url="redis://localhost:6379/1",
        environment="test",
        log_level="DEBUG"
    )


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    mock_client = Mock()
    mock_client.table.return_value = Mock()
    return mock_client


@pytest.fixture
def sample_incident_data():
    """Sample incident data for testing."""
    return {
        "id": "test-incident-id",
        "user_id": "test-user-id",
        "status": "pending",
        "story_text": "encrypted-story",
        "extracted_data": '{"incident_type": "car_accident", "severity": "medium"}',
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }


@pytest.fixture
def sample_story_text():
    """Sample incident story text."""
    return """
    My car was hit in a parking lot on January 15th, 2024 at 3:30 PM.
    The incident occurred at 123 Main Street, Downtown.
    The other driver's license plate was ABC-1234.
    I have a police report and photos of the damage.
    """


@pytest.fixture
def sample_extraction_result():
    """Sample LLM extraction result."""
    return {
        "incident_type": "car_accident",
        "severity": "medium",
        "date": "2024-01-15",
        "location": "123 Main Street, Downtown",
        "people_involved": [],
        "documents_detected": ["police_report"],
        "confidence": 0.85,
        "needs_human": False
    }


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJleHAiOjE5OTk5OTk5OTl9.test"


@pytest.fixture
def sample_pii_mapping():
    """Sample PII pseudonymization mapping."""
    return {
        "john.doe@example.com": "[EMAIL_1]",
        "555-123-4567": "[PHONE_1]",
        "123-45-6789": "[SSN_1]"
    }
