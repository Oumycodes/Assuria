# Assura Architecture Documentation

## Overview

Assura is an invisible insurance assistant backend that processes free-text incident stories and documents, extracts structured information using AI, verifies coverage, and escalates to humans when necessary.

## System Architecture

```
┌─────────────┐
│   Frontend  │ (Lovable - API only)
│  (Lovable)  │
└──────┬──────┘
       │ HTTPS + JWT
       │
┌──────▼─────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  POST /incident                               │  │
│  │  GET /incident/{id}                           │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Middleware: JWT Auth (Supabase)              │  │
│  └──────────────────────────────────────────────┘  │
└──────┬─────────────────────────────────────────────┘
       │
       ├─────────────────┬─────────────────┬──────────┐
       │                 │                 │          │
┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌─▼────────┐
│   Services  │  │   Workers   │  │  Database   │  │  Storage  │
│             │  │  (Celery)   │  │ (Supabase)  │  │(Supabase) │
│ - LLM       │  │             │  │             │  │           │
│ - CV        │  │ - Coverage  │  │ - Incidents │  │ - Files   │
│ - Encryption│  │ - Severity  │  │ - Events    │  │           │
│ - PII       │  │ - Escalate  │  │ - Documents │  │           │
└─────────────┘  └─────────────┘  └─────────────┘  └───────────┘
       │
       │
┌──────▼──────┐
│  External   │
│             │
│ - Claude    │
│ - Tesseract │
└─────────────┘
```

## Data Flow

### 1. Incident Submission

```
User → POST /incident
  ↓
[Auth Middleware] Verify JWT, extract user_id
  ↓
[PII Service] Pseudonymize story text
  ↓
[CV Service] Process attachments (OCR, analysis)
  ↓
[LLM Service] Extract structured JSON via Claude
  ↓
[Encryption Service] Encrypt PII fields
  ↓
[Database] Store incident
  ↓
[Celery Worker] Trigger background processing
  ↓
Response: incident_id, status, extracted_data
```

### 2. Background Processing

```
Celery Worker receives incident_id
  ↓
[Coverage Verification] Check if incident type is covered
  ↓
[Severity Classification] Verify/update severity
  ↓
[Escalation Check] confidence < 0.6 or missing fields?
  ├─ Yes → Escalate to human
  └─ No → Continue
  ↓
[Follow-ups] Trigger automated emails/notifications
  ↓
[Timeline] Update with events
  ↓
[Database] Update status to "verified" or "escalated"
```

## Security Architecture

### Encryption Layers

1. **PII Redaction**: Before LLM processing
   - Pseudonymization: `[EMAIL_1]`, `[PHONE_1]`
   - Mapping stored encrypted in DB

2. **Field-level Encryption**: Before database storage
   - Fernet (AES-128) symmetric encryption
   - Only PII fields encrypted
   - Key stored in environment variable

3. **Database Security**:
   - Row-level security (RLS) policies
   - Users can only access their own incidents
   - Service role key for backend operations

### Data Privacy

- **LLM Processing**: Only sees pseudonymized data
- **Storage**: PII encrypted at rest
- **Transmission**: HTTPS only
- **Access Control**: JWT-based, RLS-enforced

## Database Schema

### Core Tables

1. **incidents**
   - Stores encrypted story text
   - JSONB for extracted_data (with encrypted PII fields)
   - Status tracking

2. **claim_events**
   - Timeline of events
   - Metadata for each event

3. **documents**
   - File metadata
   - CV extraction results
   - Links to Supabase Storage

4. **human_corrections**
   - Stores human feedback
   - Used for safe learning (few-shot prompts)

5. **embeddings**
   - Vector embeddings for RAG
   - pgvector for similarity search

## LLM Integration

### Claude API Usage

**Model**: `claude-3-5-sonnet-20241022`

**Prompt Strategy**:
- Strict JSON output requirement
- Never invent information
- Confidence scoring
- Needs_human flag for low confidence

**Extraction Schema**:
```json
{
  "incident_type": "string",
  "severity": "low | medium | high",
  "date": "string",
  "location": "string",
  "people_involved": ["array"],
  "documents_detected": ["array"],
  "confidence": 0.0-1.0,
  "needs_human": boolean
}
```

## Computer Vision Pipeline

### Image Processing
- OCR via Tesseract
- Document type detection (police report, medical record, etc.)
- Basic damage detection (edge detection)

### PDF Processing
- Text extraction via PyPDF2
- Document type classification
- Multi-page support

### Video Processing
- Frame extraction (every 30th frame)
- OCR on key frames
- Metadata extraction (duration, FPS, dimensions)

## Background Workers

### Celery Configuration
- Broker: Redis
- Serialization: JSON
- Concurrency: 4 workers (configurable)

### Task: `process_incident`
1. Coverage verification
2. Severity classification
3. Escalation check
4. Follow-up triggers
5. Timeline updates

## Error Handling

### LLM Failures
- JSON parse errors → Return safe default with `needs_human: true`
- API errors → Log and escalate

### CV Failures
- OCR failures → Continue with available data
- File format errors → Log and skip

### Database Failures
- Connection errors → Retry with exponential backoff
- RLS violations → Return 403 Forbidden

## Scalability Considerations

### Current Design
- Stateless API servers (horizontal scaling)
- Celery workers (horizontal scaling)
- Redis for task queue
- Supabase for database (managed scaling)

### Future Enhancements
- CDN for file storage
- Message queue (RabbitMQ) for high volume
- Caching layer (Redis) for frequent queries
- Load balancer for API servers

## Monitoring & Observability

### Logging
- Structured logging with levels
- Request/response logging
- Worker task logging

### Metrics (Future)
- API response times
- Task processing times
- Error rates
- LLM API usage/costs

## Deployment

### Development
```bash
uvicorn app.main:app --reload
celery -A app.celery_app worker --loglevel=info
```

### Production
- Use gunicorn with uvicorn workers
- Celery with multiple workers
- Redis cluster
- Environment-based configuration
- Health check endpoints

## Testing Strategy

### Unit Tests
- Service layer (encryption, PII, LLM mocking)
- Utility functions

### Integration Tests
- API endpoints (with test database)
- Worker tasks (with test broker)

### E2E Tests
- Full incident submission flow
- Background processing flow

## Future Enhancements

1. **Enhanced CV**: ML models for damage detection
2. **RAG System**: Use embeddings for few-shot learning
3. **Multi-language**: Support non-English stories
4. **Real-time Updates**: WebSocket for status updates
5. **Analytics**: Dashboard for claim metrics
6. **Policy Integration**: Real policy database lookup
