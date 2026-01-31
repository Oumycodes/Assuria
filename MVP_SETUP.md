# MVP Setup Guide - No Database Required

This guide shows how to run Assura backend in MVP mode with in-memory storage, no Supabase or external dependencies needed.

## Quick Start

### 1. Install Dependencies (Minimal)

**Absolute minimum (server starts, all core features work):**
```bash
pip install fastapi uvicorn python-dotenv pydantic pydantic-settings python-multipart
```

This minimal install gives you:
- ✅ Server starts and runs
- ✅ All API endpoints work
- ✅ In-memory database
- ✅ Synchronous workers (no Celery/Redis needed)
- ✅ No-op encryption
- ❌ CV features disabled (install Pillow/pytesseract/PyPDF2/opencv-python if needed)

**With CV features (optional - for image/PDF/video processing):**
```bash
pip install Pillow opencv-python pytesseract PyPDF2
```

**Full install (all features):**
```bash
pip install -r requirements.txt
```

**Note:** All CV dependencies (Pillow, OpenCV, pytesseract, PyPDF2) are optional. The server will start without them, but image/PDF/video processing will be disabled.

### 2. Run the Server

```bash
# Option 1: Use the MVP script
python run_mvp.py

# Option 2: Direct uvicorn
uvicorn app.main:app --reload
```

The server will start with in-memory database automatically!

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create incident (no auth token needed in MVP mode)
curl -X POST "http://localhost:8000/incident" \
  -F "story_text=My car was hit in a parking lot on January 15th, 2024"

# Get incident (use the incident_id from previous response)
curl "http://localhost:8000/incident/INCIDENT_ID"
```

## How It Works

### In-Memory Database

- All data stored in Python dictionaries
- No persistence (data lost on restart)
- Perfect for testing and MVP

### No-Op Encryption

- Encryption service uses no-op mode in MVP
- Data stored as-is (no Fernet encryption)
- No encryption key required
- Perfect for testing without security overhead

### Authentication

- MVP mode accepts any token or no token
- Defaults to `test-user-123` if no token provided
- Real Supabase auth still works if configured

### Background Workers

- Workers run synchronously in MVP mode
- No Celery/Redis required
- Processing happens immediately

## Configuration

The system automatically detects MVP mode when:
- `use_memory_db=true` in config (default)
- Supabase URL is not configured
- Supabase package is not installed

## Testing with Frontend (Lovable)

1. Start the backend:
   ```bash
   python run_mvp.py
   ```

2. In Lovable, set API base URL to: `http://localhost:8000`

3. For authentication, use any token:
   - `test-token`
   - `test-user-123`
   - Or omit the Authorization header

4. Test endpoints:
   - `POST /incident` - Create incident
   - `GET /incident/{id}` - Get incident

## Example API Calls

### Create Incident

```bash
curl -X POST "http://localhost:8000/incident" \
  -H "Content-Type: multipart/form-data" \
  -F "story_text=My car was damaged in an accident on January 15th, 2024 at 123 Main Street. The other driver's license plate was ABC-1234."
```

Response:
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

### Get Incident

```bash
curl "http://localhost:8000/incident/INCIDENT_ID"
```

### With File Attachment

```bash
curl -X POST "http://localhost:8000/incident" \
  -F "story_text=See attached damage photos" \
  -F "files=@damage_photo.jpg"
```

## Switching to Real Database

When ready to use Supabase:

1. Set in `.env`:
   ```bash
   USE_MEMORY_DB=false
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-key
   ```

2. Restart the server

## Limitations of MVP Mode

- Data is lost on server restart
- No real authentication
- No encryption (data stored as plain text)
- Workers run synchronously (may slow down API)
- No file storage (attachments metadata only)

## Troubleshooting

### "Module not found" errors

Some optional dependencies may be missing. Install only what you need:
- For LLM: `anthropic`
- For CV: `opencv-python`, `pytesseract`, `PyPDF2`, `Pillow`
- For encryption: `cryptography`

### Workers not processing

In MVP mode, workers run synchronously. Check server logs for processing messages.

### Data disappears

This is expected - in-memory database doesn't persist. Restart = fresh data.
