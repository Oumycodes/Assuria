"""
Unit tests for LLM service (Claude integration).
Tests use mocks to avoid actual API calls.
"""

import pytest
from unittest.mock import Mock, patch
from app.services.llm_service import (
    extract_incident_data,
    validate_extraction,
    merge_extractions
)


@patch('app.services.llm_service._client')
def test_extract_incident_data_success(mock_client, sample_story_text):
    """Test successful incident data extraction."""
    # Mock Claude API response
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = '''{
        "incident_type": "car_accident",
        "severity": "medium",
        "date": "2024-01-15",
        "location": "123 Main Street",
        "people_involved": [],
        "documents_detected": [],
        "confidence": 0.85,
        "needs_human": false
    }'''
    
    mock_client.messages.create.return_value = mock_response
    
    result = extract_incident_data(sample_story_text)
    
    assert result["incident_type"] == "car_accident"
    assert result["severity"] == "medium"
    assert result["confidence"] == 0.85
    assert result["needs_human"] == False


@patch('app.services.llm_service._client')
def test_extract_incident_data_low_confidence(mock_client):
    """Test extraction with low confidence triggers needs_human."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = '''{
        "incident_type": "unknown",
        "severity": "low",
        "date": null,
        "location": null,
        "people_involved": [],
        "documents_detected": [],
        "confidence": 0.3,
        "needs_human": true
    }'''
    
    mock_client.messages.create.return_value = mock_response
    
    result = extract_incident_data("Vague story")
    
    assert result["confidence"] == 0.3
    assert result["needs_human"] == True


@patch('app.services.llm_service._client')
def test_extract_incident_data_invalid_json(mock_client):
    """Test handling of invalid JSON response."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = "This is not JSON"
    
    mock_client.messages.create.return_value = mock_response
    
    result = extract_incident_data("Test story")
    
    # Should return safe default
    assert result["needs_human"] == True
    assert result["confidence"] == 0.0


def test_validate_extraction_valid():
    """Test validation of valid extraction."""
    data = {
        "incident_type": "car_accident",
        "severity": "medium",
        "date": "2024-01-15",
        "location": "123 Main St",
        "confidence": 0.8,
        "needs_human": False
    }
    
    assert validate_extraction(data) == True


def test_validate_extraction_missing_field():
    """Test validation fails with missing field."""
    data = {
        "incident_type": "car_accident",
        "severity": "medium",
        # Missing date
        "location": "123 Main St",
        "confidence": 0.8,
        "needs_human": False
    }
    
    assert validate_extraction(data) == False


def test_validate_extraction_low_confidence():
    """Test validation fails with low confidence."""
    data = {
        "incident_type": "car_accident",
        "severity": "medium",
        "date": "2024-01-15",
        "location": "123 Main St",
        "confidence": 0.4,  # Below threshold
        "needs_human": False
    }
    
    assert validate_extraction(data) == False


def test_merge_extractions():
    """Test merging text and CV extractions."""
    text_extraction = {
        "incident_type": "car_accident",
        "documents_detected": ["police_report"],
        "confidence": 0.8
    }
    
    cv_extraction = {
        "documents_detected": ["receipt", "police_report"],
        "confidence": 0.7
    }
    
    merged = merge_extractions(text_extraction, cv_extraction)
    
    assert "police_report" in merged["documents_detected"]
    assert "receipt" in merged["documents_detected"]
    assert merged["confidence"] == 0.8  # Max of both
