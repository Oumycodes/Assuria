"""
Incident management routes.
POST /incident - Create new incident
GET /incident/{id} - Get incident details
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import logging
from datetime import datetime
import json

from app.middleware.auth import get_current_user_id
from app.database import get_supabase_client
from app.services.encryption_service import encrypt_field, decrypt_field, encrypt_dict_fields
from app.services.pii_service import pseudonymize_pii, extract_pii_fields
from app.services.llm_service import extract_incident_data, merge_extractions
from app.services.cv_service import process_attachments
from app.models import IncidentStatus, IncidentResponse
from app.workers.incident_worker import process_incident_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incident", tags=["incidents"])


@router.post("", status_code=201)
async def create_incident(
    story_text: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new incident from free-text story and optional attachments.
    
    Process:
    1. Redact/pseudonymize PII from story
    2. Process attachments (OCR, CV analysis)
    3. Extract structured data via Claude
    4. Encrypt PII fields
    5. Store in database
    6. Trigger background worker for verification/escalation
    """
    supabase = get_supabase_client()
    
    try:
        # Step 1: Pseudonymize PII from story
        pseudonymized_story, pii_mapping = pseudonymize_pii(story_text)
        logger.info(f"Pseudonymized story for user {user_id}")
        
        # Step 2: Process attachments if provided
        cv_metadata = None
        attachment_data = []
        
        if files:
            for file in files:
                content = await file.read()
                attachment_data.append({
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "data": content
                })
            
            # Process attachments with CV pipeline
            cv_metadata = process_attachments(attachment_data)
            logger.info(f"Processed {len(attachment_data)} attachments")
        
        # Step 3: Extract structured data via Claude
        extracted_data = extract_incident_data(pseudonymized_story, cv_metadata)
        
        # Merge CV and text extractions
        if cv_metadata:
            cv_extraction = {
                "documents_detected": cv_metadata.get("documents_detected", []),
                "confidence": cv_metadata.get("confidence", 0.0)
            }
            extracted_data = merge_extractions(extracted_data, cv_extraction)
        
        # Step 4: Identify PII fields in extracted data
        pii_fields = extract_pii_fields(extracted_data)
        
        # Step 5: Encrypt PII fields before storage
        encrypted_extracted = encrypt_dict_fields(extracted_data, list(pii_fields.keys()))
        
        # Also encrypt the story text
        encrypted_story = encrypt_field(pseudonymized_story)
        
        # Step 6: Store in database
        incident_data = {
            "user_id": user_id,
            "status": IncidentStatus.PENDING.value,
            "story_text": encrypted_story,
            "extracted_data": json.dumps(encrypted_extracted),
            "pii_mapping": json.dumps(pii_mapping),  # Store mapping for restoration
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("incidents").insert(incident_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create incident")
        
        incident_id = result.data[0]["id"]
        logger.info(f"Created incident {incident_id} for user {user_id}")
        
        # Step 7: Store attachments metadata
        if attachment_data:
            for idx, attachment in enumerate(attachment_data):
                # In production, upload to Supabase Storage and store encrypted URLs
                # For MVP, store metadata
                doc_data = {
                    "incident_id": incident_id,
                    "filename": attachment["filename"],
                    "content_type": attachment["content_type"],
                    "file_size": len(attachment["data"]),
                    "created_at": datetime.utcnow().isoformat()
                }
                supabase.table("documents").insert(doc_data).execute()
        
        # Step 8: Create initial timeline event
        timeline_event = {
            "incident_id": incident_id,
            "event_type": "incident_created",
            "description": "Incident submitted and initial extraction completed",
            "metadata": json.dumps({
                "confidence": extracted_data.get("confidence", 0.0),
                "needs_human": extracted_data.get("needs_human", False)
            }),
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("claim_events").insert(timeline_event).execute()
        
        # Step 9: Trigger background worker (async)
        process_incident_async.delay(incident_id)
        
        # Return response
        return {
            "incident_id": incident_id,
            "status": IncidentStatus.PENDING.value,
            "extracted_data": extracted_data,  # Return decrypted for user
            "message": "Incident created successfully. Processing in background."
        }
        
    except Exception as e:
        logger.error(f"Error creating incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create incident: {str(e)}")


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get incident details by ID.
    Only returns incidents belonging to the authenticated user.
    """
    supabase = get_supabase_client()
    
    try:
        # Fetch incident (RLS ensures user can only see their own)
        result = supabase.table("incidents").select("*").eq("id", incident_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        incident = result.data[0]
        
        # Decrypt story text
        encrypted_story = incident.get("story_text")
        if encrypted_story:
            incident["story_text"] = decrypt_field(encrypted_story)
        
        # Decrypt extracted data
        encrypted_extracted = json.loads(incident.get("extracted_data", "{}"))
        pii_fields = extract_pii_fields(encrypted_extracted)
        incident["extracted_data"] = decrypt_dict_fields(encrypted_extracted, list(pii_fields.keys()))
        
        # Fetch timeline events
        events_result = supabase.table("claim_events").select("*").eq("incident_id", incident_id).order("created_at").execute()
        incident["timeline"] = events_result.data if events_result.data else []
        
        # Parse metadata in timeline events
        for event in incident["timeline"]:
            if event.get("metadata"):
                try:
                    event["metadata"] = json.loads(event["metadata"])
                except:
                    pass
        
        return IncidentResponse(**incident)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch incident: {str(e)}")
