# Quick Testing Guide

## Setup (One-time)

```bash
# Install test dependencies
pip install -r requirements-dev.txt
```

## Run Tests

```bash
# All unit tests
pytest tests/unit/ -v

# All integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_encryption_service.py -v

# With coverage report
pytest --cov=app --cov-report=html
```

## Manual API Testing

### 1. Start Services

```bash
# Terminal 1: API Server
uvicorn app.main:app --reload

# Terminal 2: Celery Worker
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Redis (if needed)
redis-server
```

### 2. Get JWT Token

Authenticate with Supabase to get a token, or use the Supabase dashboard.

### 3. Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Create incident
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT" \
  -F "story_text=My car was hit"

# Get incident
curl "http://localhost:8000/incident/INCIDENT_ID" \
  -H "Authorization: Bearer YOUR_JWT"
```

## Common Test Scenarios

### High Confidence Story
```
"My car was hit in a parking lot on January 15th, 2024 at 3:30 PM at 123 Main Street. The other driver's license plate was ABC-1234."
```
Expected: `confidence > 0.7`, `needs_human: false`

### Low Confidence Story
```
"Something happened to my car"
```
Expected: `confidence < 0.6`, `needs_human: true`

### With PDF Attachment
```bash
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT" \
  -F "story_text=See attached report" \
  -F "files=@police_report.pdf"
```

## Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
pytest -vv -s

# Run single test
pytest tests/unit/test_encryption_service.py::test_encrypt_decrypt_field -v
```
