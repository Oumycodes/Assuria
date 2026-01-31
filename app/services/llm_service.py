"""
LLM service for Claude API integration.
Extracts structured JSON from incident stories with strict validation.
"""

import json
import logging
from typing import Dict, Any, Optional
from anthropic import Anthropic
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Claude client
_client = Anthropic(api_key=settings.anthropic_api_key)

# Strict JSON schema for incident extraction
EXTRACTION_SCHEMA = {
    "incident_type": "string",
    "severity": "low | medium | high",
    "date": "string (ISO format or natural language)",
    "location": "string",
    "people_involved": "array of strings",
    "documents_detected": "array of strings",
    "confidence": "float (0-1)",
    "needs_human": "boolean"
}


def extract_incident_data(story_text: str, cv_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract structured incident data from free-text story using Claude.
    Claude MUST return only strict JSON - no additional text.
    
    Args:
        story_text: User's free-text incident story (already redacted/pseudonymized)
        cv_metadata: Optional metadata from computer vision pipeline
        
    Returns:
        Structured JSON with incident data
    """
    
    # Build prompt with strict JSON requirement
    cv_context = ""
    if cv_metadata:
        cv_context = f"\n\nAdditional context from document analysis:\n{json.dumps(cv_metadata, indent=2)}"
    
    prompt = f"""You are an insurance claim extraction system. Extract structured information from the following incident story.

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no explanations, no code blocks
2. NEVER invent information - use "null" or empty arrays if information is not present
3. If confidence is low (< 0.6) or critical fields are missing, set needs_human = true
4. Severity must be one of: "low", "medium", "high"
5. Confidence must be a float between 0 and 1

Required JSON structure:
{{
  "incident_type": "string (e.g., 'car_accident', 'property_damage', 'theft', etc.)",
  "severity": "low | medium | high",
  "date": "string (ISO format preferred, or natural language if exact date unknown)",
  "location": "string (address, city, or description)",
  "people_involved": ["array", "of", "names", "or", "descriptions"],
  "documents_detected": ["array", "of", "document", "types", "found"],
  "confidence": 0.0-1.0,
  "needs_human": true/false
}}

Incident story:
{story_text}{cv_context}

Return ONLY the JSON object:"""

    try:
        # Call Claude API
        message = _client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.1,  # Low temperature for consistent extraction
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        extracted_data = json.loads(response_text)
        
        # Validate required fields
        if not validate_extraction(extracted_data):
            logger.warning("Extraction validation failed, setting needs_human = true")
            extracted_data["needs_human"] = True
        
        return extracted_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude JSON response: {e}")
        logger.error(f"Response was: {response_text[:500]}")
        # Return safe default
        return {
            "incident_type": None,
            "severity": "medium",
            "date": None,
            "location": None,
            "people_involved": [],
            "documents_detected": [],
            "confidence": 0.0,
            "needs_human": True
        }
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise


def validate_extraction(data: Dict[str, Any]) -> bool:
    """
    Validate extracted data meets requirements.
    
    Args:
        data: Extracted incident data
        
    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    required_fields = ["incident_type", "severity", "date", "location", "confidence", "needs_human"]
    for field in required_fields:
        if field not in data:
            return False
    
    # Check severity is valid
    if data["severity"] not in ["low", "medium", "high"]:
        return False
    
    # Check confidence range
    confidence = data.get("confidence", 0)
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        return False
    
    # Check critical fields (from config)
    for field in settings.critical_fields:
        if not data.get(field):
            return False
    
    # Check confidence threshold
    if confidence < settings.min_confidence_threshold:
        return False
    
    return True


def merge_extractions(text_extraction: Dict[str, Any], cv_extraction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge text-based extraction with CV extraction.
    CV data takes precedence for document detection, text for narrative fields.
    
    Args:
        text_extraction: Extraction from Claude on text
        cv_extraction: Extraction from computer vision pipeline
        
    Returns:
        Merged extraction
    """
    merged = text_extraction.copy()
    
    # Merge documents_detected (combine both sources)
    text_docs = set(text_extraction.get("documents_detected", []))
    cv_docs = set(cv_extraction.get("documents_detected", []))
    merged["documents_detected"] = list(text_docs | cv_docs)
    
    # Use CV data to enhance confidence if it provides additional info
    if cv_extraction.get("confidence", 0) > 0:
        # Average confidence or use higher
        merged["confidence"] = max(
            text_extraction.get("confidence", 0),
            cv_extraction.get("confidence", 0)
        )
    
    # Update needs_human if either source requires it
    if cv_extraction.get("needs_human", False):
        merged["needs_human"] = True
    
    return merged
