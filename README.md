# Assura - Invisible Insurance Assistant Backend

A production-ready backend MVP for an invisible insurance assistant that processes free-text incident stories and documents, extracts structured information, verifies coverage, and escalates to humans when needed.

## Architecture

**Tech Stack:**
- **Backend**: Python + FastAPI
- **Database**: Supabase Postgres + pgvector
- **Auth**: Supabase Auth (JWT)
- **Encryption**: Field-level AES/Fernet for PII
- **LLM**: Claude API (Anthropic)
- **Computer Vision**: OpenCV / PyTorch / OCR (Tesseract)
- **Background Tasks**: Celery + Redis
- **Frontend**: Lovable (API-only)

## Features

1. **Incident Processing**
   - Accepts free-text stories and attachments (images, PDFs, videos)
   - Redacts/pseudonymizes PII before LLM processing
   - Extracts structured JSON via Claude API
   - Computer vision pipeline for document analysis
   - Field-level encryption for sensitive data

2. **Background Workers (Moltbot-style)**
   - Coverage verification
   - Severity classification
   - Automated follow-ups
   - Escalation when confidence < 0.6 or critical fields missing

3. **Security & Compliance**
   - GDPR-compliant PII handling
   - Row-level security (RLS) in Supabase
   - Encrypted storage for sensitive fields
   - LLM only sees anonymized data

4. **Safe Learning**
   - Stores human corrections
   - Feedback table for improvements
   - RAG-ready embeddings table

## Setup

### 1. Prerequisites

- Python 3.10+
- Supabase account and project
- Redis (for Celery)
- Anthropic API key
- Tesseract OCR (for image text extraction)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Install Tesseract OCR:**
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt-get install tesseract-ocr`
- Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required variables:**
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key (for backend operations)
- `SUPABASE_DB_URL`: PostgreSQL connection string
- `ENCRYPTION_KEY`: Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `ANTHROPIC_API_KEY`: Your Claude API key
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)

### 4. Database Setup

1. Open your Supabase project dashboard
2. Go to SQL Editor
3. Run the migration file: `migrations/schema.sql`
4. Create a storage bucket named `incident-attachments` (or modify the code)

### 5. Run the Application

**Start the API server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Celery worker (in separate terminal):**
```bash
celery -A app.workers.incident_worker worker --loglevel=info
```

**Start Redis (if not running):**
```bash
redis-server
```

## API Endpoints

### POST /incident

Create a new incident from free-text story and optional attachments.

**Request:**
- `story_text` (form-data): Free-text incident story
- `files` (form-data, optional): Attachments (images, PDFs, videos)

**Response:**
```json
{
  "incident_id": "uuid",
  "status": "pending",
  "extracted_data": {
    "incident_type": "car_accident",
    "severity": "medium",
    "date": "2024-01-15",
    "location": "123 Main St",
    "people_involved": ["John Doe"],
    "documents_detected": ["police_report"],
    "confidence": 0.85,
    "needs_human": false
  },
  "message": "Incident created successfully. Processing in background."
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "story_text=My car was hit in a parking lot on January 15th" \
  -F "files=@/path/to/police_report.pdf"
```

### GET /incident/{id}

Get incident details with timeline.

**Response:**
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
    },
    {
      "event_type": "coverage_verified",
      "description": "Coverage verified",
      "created_at": "2024-01-15T10:01:00Z"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:02:00Z"
}
```

## Architecture Details

### Data Flow

1. **User submits incident** → POST /incident
2. **PII redaction** → Story text pseudonymized
3. **CV processing** → OCR, document analysis on attachments
4. **LLM extraction** → Claude extracts structured JSON
5. **Encryption** → PII fields encrypted before storage
6. **Database storage** → Incident stored in Supabase
7. **Background worker** → Coverage verification, escalation, follow-ups

### Security Model

- **Authentication**: Supabase JWT tokens
- **Authorization**: RLS policies ensure users only see their data
- **Encryption**: Field-level Fernet encryption for PII
- **LLM Privacy**: Only pseudonymized data sent to Claude
- **Storage**: Encrypted files in Supabase Storage

### LLM Extraction Schema

Claude returns strict JSON:
```json
{
  "incident_type": "string",
  "severity": "low | medium | high",
  "date": "string",
  "location": "string",
  "people_involved": ["array"],
  "documents_detected": ["array"],
  "confidence": 0.0-1.0,
  "needs_human": true/false
}
```

### Background Worker Flow

1. Verify coverage (check incident type)
2. Classify/verify severity
3. Check escalation criteria:
   - Confidence < 0.6
   - Missing critical fields
   - `needs_human` flag
4. Trigger follow-ups (email/notifications)
5. Update timeline and status

## Testing

See [TESTING.md](TESTING.md) for comprehensive testing guide.

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run unit tests
pytest tests/unit/ -v

# Run integration tests (requires test database)
pytest tests/integration/ -v

# Run all tests with coverage
pytest --cov=app --cov-report=html
```

### Manual API Testing

```bash
# Start server
uvicorn app.main:app --reload

# Test health endpoint
curl http://localhost:8000/health

# Create incident (requires JWT token)
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "story_text=My car was hit in a parking lot"
```

## Development

### Project Structure

```
assura/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # Supabase client
│   ├── models.py            # Pydantic models
│   ├── middleware/
│   │   └── auth.py          # JWT authentication
│   ├── routes/
│   │   └── incidents.py     # API routes
│   ├── services/
│   │   ├── encryption_service.py  # PII encryption
│   │   ├── pii_service.py         # PII redaction
│   │   ├── llm_service.py         # Claude integration
│   │   └── cv_service.py          # Computer vision
│   └── workers/
│       └── incident_worker.py     # Celery tasks
├── migrations/
│   └── schema.sql           # Database schema
├── requirements.txt
├── .env.example
└── README.md
```

### Testing

```bash
# Run API server
uvicorn app.main:app --reload

# Test endpoint (requires valid JWT)
curl -X POST "http://localhost:8000/incident" \
  -H "Authorization: Bearer YOUR_JWT" \
  -F "story_text=Test incident"
```

### Monitoring

- Check Celery worker logs for background processing
- Monitor Supabase dashboard for database activity
- Review API logs for errors

## Production Considerations

1. **Environment Variables**: Use secure secret management (AWS Secrets Manager, etc.)
2. **Rate Limiting**: Add rate limiting to API endpoints
3. **Error Handling**: Enhance error messages and logging
4. **File Storage**: Implement proper file upload to Supabase Storage
5. **Email/Notifications**: Integrate SendGrid, SES, or similar
6. **Monitoring**: Add APM (Datadog, New Relic, etc.)
7. **Scaling**: Use Celery with multiple workers, Redis cluster
8. **Backup**: Regular database backups via Supabase

## License

Proprietary - All rights reserved
