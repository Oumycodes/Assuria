"""
Database models and data structures for Assura.
These represent the structure of data stored in Supabase.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class Severity(str, Enum):
    """Incident severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IncidentStatus(str, Enum):
    """Incident processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VERIFIED = "verified"
    ESCALATED = "escalated"
    CLOSED = "closed"


class IncidentCreate(BaseModel):
    """Request model for creating an incident."""
    story_text: str = Field(..., description="Free-text incident story")
    attachments: Optional[List[str]] = Field(default=[], description="Attachment IDs (uploaded separately)")


class IncidentResponse(BaseModel):
    """Response model for incident data."""
    id: str
    user_id: str
    status: IncidentStatus
    story_text: Optional[str] = None  # Encrypted in DB, decrypted here
    extracted_data: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ExtractionResult(BaseModel):
    """Structured extraction from LLM."""
    incident_type: Optional[str] = None
    severity: Severity
    date: Optional[str] = None
    location: Optional[str] = None
    people_involved: List[str] = Field(default_factory=list)
    documents_detected: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_human: bool = False


class ClaimEvent(BaseModel):
    """Timeline event for an incident."""
    event_type: str
    description: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class HumanCorrection(BaseModel):
    """Human feedback/correction for learning."""
    incident_id: str
    field_name: str
    original_value: Any
    corrected_value: Any
    corrected_by: str
    created_at: datetime
