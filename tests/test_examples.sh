#!/bin/bash
# Example manual test scripts for Assura API

# Configuration
API_URL="http://localhost:8000"
JWT_TOKEN="YOUR_JWT_TOKEN_HERE"  # Replace with actual token

echo "=== Testing Assura API ==="
echo ""

# Test 1: Health Check
echo "1. Testing health endpoint..."
curl -s "$API_URL/health" | jq .
echo ""

# Test 2: Create Incident (No Attachments)
echo "2. Creating incident without attachments..."
INCIDENT_RESPONSE=$(curl -s -X POST "$API_URL/incident" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "story_text=My car was hit in a parking lot on January 15th, 2024 at 123 Main Street. The other driver's license plate was ABC-1234.")

echo "$INCIDENT_RESPONSE" | jq .
INCIDENT_ID=$(echo "$INCIDENT_RESPONSE" | jq -r '.incident_id')
echo "Incident ID: $INCIDENT_ID"
echo ""

# Test 3: Get Incident Details
if [ "$INCIDENT_ID" != "null" ] && [ -n "$INCIDENT_ID" ]; then
  echo "3. Getting incident details..."
  curl -s -X GET "$API_URL/incident/$INCIDENT_ID" \
    -H "Authorization: Bearer $JWT_TOKEN" | jq .
  echo ""
fi

# Test 4: Create Incident with Image (if file exists)
if [ -f "test_image.jpg" ]; then
  echo "4. Creating incident with image attachment..."
  curl -s -X POST "$API_URL/incident" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -F "story_text=Damage to my vehicle" \
    -F "files=@test_image.jpg" | jq .
  echo ""
fi

echo "=== Tests Complete ==="
