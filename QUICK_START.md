# Quick Start - MVP Mode

Get Assura backend running in 2 minutes with no database setup!

## Step 1: Install Dependencies

**Absolute minimum (server starts, all features work in sync mode):**
```bash
pip install fastapi uvicorn python-dotenv pydantic pydantic-settings python-multipart
```

This will start the server with:
- ✅ In-memory database
- ✅ No-op encryption
- ✅ Synchronous workers (no Celery needed)
- ✅ All API endpoints working
- ❌ CV features disabled (install Pillow/pytesseract/PyPDF2/opencv-python if needed)

**With CV features (optional):**
```bash
pip install Pillow opencv-python pytesseract PyPDF2
```

**Full install (all features):**
```bash
pip install -r requirements.txt
```

**Note:** The server will start even without CV dependencies - those features will just be disabled.

## Step 2: Run the Server

```bash
python run_mvp.py
```

That's it! The server is now running at `http://localhost:8000`

## Step 3: Test It

### Option A: Use the test script

```bash
# In another terminal
bash test_mvp.sh
```

### Option B: Manual testing

```bash
# Health check
curl http://localhost:8000/health

# Create incident
curl -X POST "http://localhost:8000/incident" \
  -F "story_text=My car was hit in a parking lot on January 15th, 2024"

# Get incident (use ID from previous response)
curl "http://localhost:8000/incident/INCIDENT_ID"
```

### Option C: Use the API docs

Open in browser: `http://localhost:8000/docs`

## What Works in MVP Mode

✅ Create incidents with free-text stories  
✅ Upload attachments (images, PDFs, videos)  
✅ Get incident details with timeline  
✅ Background processing (synchronous)  
✅ LLM extraction (if Anthropic API key set)  
✅ Computer vision (if dependencies installed)  
✅ PII redaction (encryption is no-op in MVP mode)  

## What's Different

- **No database**: Data stored in memory (lost on restart)
- **No real auth**: Accepts any token or defaults to test user
- **Synchronous workers**: No Celery/Redis needed
- **No file storage**: Attachment metadata only

## Next Steps

1. **Test with frontend**: Point Lovable to `http://localhost:8000`
2. **Add real API key**: Set `ANTHROPIC_API_KEY` in `.env` for real LLM
3. **Switch to Supabase**: See `MVP_SETUP.md` for instructions

## Troubleshooting

**Port already in use?**
```bash
uvicorn app.main:app --reload --port 8001
```

**Missing dependencies?**
Install only what you need - most features work without optional packages.

**Want to see logs?**
Check the terminal where you ran `python run_mvp.py`
