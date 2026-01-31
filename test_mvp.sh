#!/bin/bash
# Quick test script for MVP mode

API_URL="http://localhost:8000"

echo "Testing Assura MVP Backend"
echo "=========================="
echo ""

# Test 1: Health check
echo "1. Health check..."
curl -s "$API_URL/health" | python -m json.tool
echo ""

# Test 2: Create incident
echo "2. Creating incident..."
RESPONSE=$(curl -s -X POST "$API_URL/incident" \
  -F "story_text=My car was hit in a parking lot on January 15th, 2024 at 123 Main Street. The other driver's license plate was ABC-1234.")

echo "$RESPONSE" | python -m json.tool

# Extract incident ID
INCIDENT_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('incident_id', ''))")

if [ -n "$INCIDENT_ID" ] && [ "$INCIDENT_ID" != "null" ]; then
    echo ""
    echo "Incident ID: $INCIDENT_ID"
    echo ""
    
    # Test 3: Get incident
    echo "3. Getting incident details..."
    curl -s "$API_URL/incident/$INCIDENT_ID" | python -m json.tool
    echo ""
else
    echo "Failed to create incident"
fi

echo "=========================="
echo "Tests complete!"
