"""
Background worker for processing incidents (Moltbot-style).
Handles coverage verification, severity classification, automated actions, and escalation.
"""

from app.celery_app import celery_app
from app.database import get_supabase_client
from app.models import IncidentStatus
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


@celery_app.task(name="process_incident", bind=True)
def process_incident_async(self, incident_id: str):
    """
    Background task to process an incident after initial extraction.
    
    Actions:
    1. Verify coverage (check if incident type is covered)
    2. Classify severity (may update if needed)
    3. Trigger automated follow-ups
    4. Update timeline
    5. Escalate if confidence < threshold or critical fields missing
    """
    supabase = get_supabase_client()
    
    try:
        logger.info(f"Processing incident {incident_id}")
        
        # Fetch incident
        result = supabase.table("incidents").select("*").eq("id", incident_id).execute()
        
        if not result.data:
            logger.error(f"Incident {incident_id} not found")
            return
        
        incident = result.data[0]
        extracted_data = json.loads(incident.get("extracted_data", "{}"))
        status = incident.get("status")
        
        # Update status to processing
        supabase.table("incidents").update({
            "status": IncidentStatus.PROCESSING.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", incident_id).execute()
        
        # Add timeline event
        add_timeline_event(incident_id, "processing_started", "Background processing started")
        
        # Step 1: Verify coverage
        coverage_result = verify_coverage(extracted_data)
        
        if not coverage_result["covered"]:
            add_timeline_event(
                incident_id,
                "coverage_denied",
                f"Coverage verification failed: {coverage_result['reason']}",
                {"reason": coverage_result["reason"]}
            )
            # Update status
            supabase.table("incidents").update({
                "status": IncidentStatus.ESCALATED.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", incident_id).execute()
            return
        
        add_timeline_event(
            incident_id,
            "coverage_verified",
            "Coverage verified for incident type",
            {"incident_type": extracted_data.get("incident_type")}
        )
        
        # Step 2: Classify/verify severity
        severity = classify_severity(extracted_data)
        if severity != extracted_data.get("severity"):
            extracted_data["severity"] = severity
            add_timeline_event(
                incident_id,
                "severity_updated",
                f"Severity updated to {severity}",
                {"previous": extracted_data.get("severity"), "new": severity}
            )
        
        # Step 3: Check if escalation needed
        needs_escalation = should_escalate(extracted_data)
        
        if needs_escalation:
            add_timeline_event(
                incident_id,
                "escalated",
                "Incident escalated to human agent",
                {"reason": "Low confidence or missing critical fields"}
            )
            
            supabase.table("incidents").update({
                "status": IncidentStatus.ESCALATED.value,
                "extracted_data": json.dumps(extracted_data),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", incident_id).execute()
            
            # Trigger escalation notification (email/webhook)
            trigger_escalation_notification(incident_id, incident.get("user_id"))
            return
        
        # Step 4: Trigger automated follow-ups
        trigger_follow_ups(incident_id, incident.get("user_id"), extracted_data)
        
        # Step 5: Update final status
        supabase.table("incidents").update({
            "status": IncidentStatus.VERIFIED.value,
            "extracted_data": json.dumps(extracted_data),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", incident_id).execute()
        
        add_timeline_event(
            incident_id,
            "processing_completed",
            "Incident processing completed successfully"
        )
        
        logger.info(f"Completed processing incident {incident_id}")
        
    except Exception as e:
        logger.error(f"Error processing incident {incident_id}: {e}", exc_info=True)
        
        # Mark as escalated on error
        try:
            supabase.table("incidents").update({
                "status": IncidentStatus.ESCALATED.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", incident_id).execute()
            
            add_timeline_event(
                incident_id,
                "processing_error",
                f"Error during processing: {str(e)}"
            )
        except:
            pass


def verify_coverage(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify if incident type is covered by insurance policy.
    This is a simplified version - in production, would check against policy database.
    
    Args:
        extracted_data: Extracted incident data
        
    Returns:
        Dict with 'covered' (bool) and 'reason' (str)
    """
    incident_type = extracted_data.get("incident_type", "").lower()
    
    # Covered incident types (example)
    covered_types = [
        "car_accident", "vehicle_accident", "auto_accident",
        "property_damage", "theft", "vandalism",
        "water_damage", "fire_damage", "wind_damage"
    ]
    
    # Check if incident type matches any covered type
    is_covered = any(covered in incident_type for covered in covered_types)
    
    if is_covered:
        return {"covered": True, "reason": "Incident type is covered"}
    else:
        return {
            "covered": False,
            "reason": f"Incident type '{incident_type}' may not be covered. Requires review."
        }


def classify_severity(extracted_data: Dict[str, Any]) -> str:
    """
    Classify or re-classify incident severity.
    Can enhance based on additional factors.
    
    Args:
        extracted_data: Extracted incident data
        
    Returns:
        Severity level: "low", "medium", or "high"
    """
    current_severity = extracted_data.get("severity", "medium")
    confidence = extracted_data.get("confidence", 0.5)
    
    # If confidence is very low, severity should be medium/high (needs attention)
    if confidence < 0.4:
        return "high"
    
    # Keep existing classification for now
    # Can add more sophisticated logic based on incident type, damage amount, etc.
    return current_severity


def should_escalate(extracted_data: Dict[str, Any]) -> bool:
    """
    Determine if incident should be escalated to human agent.
    
    Args:
        extracted_data: Extracted incident data
        
    Returns:
        True if should escalate, False otherwise
    """
    # Check confidence threshold
    confidence = extracted_data.get("confidence", 0.0)
    if confidence < settings.min_confidence_threshold:
        return True
    
    # Check if needs_human flag is set
    if extracted_data.get("needs_human", False):
        return True
    
    # Check critical fields
    for field in settings.critical_fields:
        if not extracted_data.get(field):
            return True
    
    return False


def trigger_follow_ups(incident_id: str, user_id: str, extracted_data: Dict[str, Any]):
    """
    Trigger automated follow-up actions (email, notifications).
    
    Args:
        incident_id: Incident ID
        user_id: User ID
        extracted_data: Extracted incident data
    """
    # Add timeline event
    add_timeline_event(
        incident_id,
        "follow_up_triggered",
        "Automated follow-up email sent to user",
        {"action": "email_sent"}
    )
    
    # In production, would send actual email via SendGrid, SES, etc.
    logger.info(f"Follow-up triggered for incident {incident_id}, user {user_id}")


def trigger_escalation_notification(incident_id: str, user_id: str):
    """
    Trigger notification when incident is escalated.
    
    Args:
        incident_id: Incident ID
        user_id: User ID
    """
    # In production, would notify human agents via Slack, email, etc.
    logger.info(f"Escalation notification for incident {incident_id}, user {user_id}")


def add_timeline_event(
    incident_id: str,
    event_type: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Add an event to the incident timeline.
    
    Args:
        incident_id: Incident ID
        event_type: Type of event
        description: Event description
        metadata: Optional metadata
    """
    supabase = get_supabase_client()
    
    event_data = {
        "incident_id": incident_id,
        "event_type": event_type,
        "description": description,
        "metadata": json.dumps(metadata) if metadata else None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    supabase.table("claim_events").insert(event_data).execute()
