# Testing Guide for Assura Backend

This guide covers how to test the Assura backend, including unit tests, integration tests, and manual API testing.

## Table of Contents

1. [Setup](#setup)
2. [Unit Tests](#unit-tests)
3. [Integration Tests](#integration-tests)
4. [Manual API Testing](#manual-api-testing)
5. [Testing Workers](#testing-workers)

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Test Configuration

Tests use a separate test database. Create a `.env.test` file:

```bash
# .env.test
SUPABASE_URL=https://your-test-project.supabase.co
SUPABASE_KEY=test-anon-key
SUPABASE_SERVICE_ROLE_KEY=test-service-role-key
SUPABASE_DB_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
ENCRYPTION_KEY=test-encryption-key  # Generate with scripts/generate_key.py
ANTHROPIC_API_KEY=test-key  # Mocked in tests
REDIS_URL=redis://localhost:6379/1  # Use different DB for tests
ENVIRONMENT=test
LOG_LEVEL=DEBUG
```

## Unit Tests

### Run All Unit Tests

```bash
pytest tests/unit/ -v
```

### Run with Coverage

```bash
pytest tests/unit/ --cov=app --cov-report=html
```

### Example Unit Tests

See `tests/unit/` directory for:
- `test_encryption_service.py` - Encryption/decryption tests
- `test_pii_service.py` - PII redaction tests
- `test_llm_service.py` - LLM service tests (mocked)
- `test_cv_service.py` - CV pipeline tests

## Integration Tests

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

**Note**: Integration tests require:
- Test Supabase database
- Redis running
- Test environment variables set

### Example Integration Tests

See `tests/integration/` directory for:
- `test_incident_api.py` - Full API endpoint tests
- `test_worker_tasks.py` - Background worker tests

## Manual API Testing

### 1. Start the Server

```bash
uvicorn app.main:app --reload
```

### 2. Get Authentication Token

First, authenticate with Supabase to get a JWT token:

```bash
# Using Supabase Auth API
curl -X POST 'https://your-project.supabase.co/auth/v1/token?grant_type=password' \
  -H "apikey: YOUR_SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your-password"
  }'
```

Save the `access_token` from the response.

### 3. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

### 4. Test Create Incident (No Attachments)

```bash
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "story_text=My car was hit in a parking lot on January 15th, 2024 at 123 Main Street. The other driver's license plate was ABC-1234."
```

Expected response:
```json
{
  "incident_id": "uuid-here",
  "status": "pending",
  "extracted_data": {
    "incident_type": "car_accident",
    "severity": "medium",
    "date": "2024-01-15",
    "location": "123 Main Street",
    "people_involved": [],
    "documents_detected": [],
    "confidence": 0.85,
    "needs_human": false
  },
  "message": "Incident created successfully. Processing in background."
}
```

### 5. Test Create Incident with PDF Attachment

```bash
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "story_text=My car was damaged in an accident. See attached police report." \
  -F "files=@/path/to/police_report.pdf"
```

### 6. Test Create Incident with Image

```bash
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "story_text=Damage to my vehicle" \
  -F "files=@/path/to/damage_photo.jpg"
```

### 7. Get Incident Details

```bash
curl -X GET "http://localhost:8000/incident/INCIDENT_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected response:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "status": "verified",
  "story_text": "My car was hit...",
  "extracted_data": {...},
  "timeline": [
    {
      "event_type": "incident_created",
      "description": "Incident submitted",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:02:00Z"
}
```

## Testing Workers

### 1. Start Redis

```bash
redis-server
```

### 2. Start Celery Worker

```bash
celery -A app.celery_app worker --loglevel=info
```

### 3. Monitor Worker Tasks

Check worker logs to see tasks being processed.

### 4. Test Worker Directly (Python)

```python
from app.workers.incident_worker import process_incident_async

# Process an incident synchronously (for testing)
process_incident_async("incident-id-here")
```

## Using Postman/Insomnia

### Import Collection

1. Create a new collection
2. Set base URL: `http://localhost:8000`
3. Add environment variable: `JWT_TOKEN`

### Endpoints to Test

1. **GET /health** - No auth required
2. **POST /incident** - Requires JWT in Authorization header
3. **GET /incident/{id}** - Requires JWT in Authorization header

### Example Postman Collection JSON

```json
{
  "info": {
    "name": "Assura API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["health"]
        }
      }
    },
    {
      "name": "Create Incident",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{JWT_TOKEN}}",
            "type": "text"
          }
        ],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "story_text",
              "value": "Test incident story",
              "type": "text"
            }
          ]
        },
        "url": {
          "raw": "http://localhost:8000/incident",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["incident"]
        }
      }
    }
  ]
}
```

## Testing Scenarios

### Scenario 1: Low Confidence Extraction

Submit a vague story:
```
"Something happened to my car"
```

Expected: `needs_human: true`, `confidence: < 0.6`

### Scenario 2: Missing Critical Fields

Submit story without date:
```
"My car was damaged at the mall"
```

Expected: Escalated to human

### Scenario 3: High Confidence Extraction

Submit detailed story:
```
"My car was hit in a parking lot on January 15th, 2024 at 3:30 PM at 123 Main Street, Downtown. The other driver's license plate was ABC-1234. I have a police report."
```

Expected: High confidence, auto-verified

### Scenario 4: Document Processing

Submit with police report PDF:
- Should detect document type
- Extract text via OCR
- Merge with story extraction

## Debugging

### Enable Debug Logging

Set in `.env`:
```
LOG_LEVEL=DEBUG
```

### Check Logs

- API logs: Console output from uvicorn
- Worker logs: Console output from Celery
- Database: Supabase dashboard > Logs

### Common Issues

1. **401 Unauthorized**: Check JWT token is valid
2. **500 Error**: Check logs, verify environment variables
3. **Worker not processing**: Check Redis connection, worker logs
4. **Encryption errors**: Verify ENCRYPTION_KEY is set correctly

## Performance Testing

### Load Testing with Apache Bench

```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_JWT" \
   -p incident_data.json -T application/json \
   http://localhost:8000/incident
```

### Load Testing with Locust

See `tests/load/locustfile.py` for example load test.

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/unit/ -v
```
