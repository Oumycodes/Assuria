# Optional Dependencies for MVP Mode

## Overview

All CV (Computer Vision) dependencies are now **optional**. The server will start and run even if these packages are not installed. Missing dependencies are handled gracefully with fallback behavior.

## Optional Dependencies

### CV/Image Processing (All Optional)

- **Pillow (PIL)** - Image processing
  - If missing: Image analysis returns basic metadata only
  - Install: `pip install Pillow`

- **pytesseract** - OCR text extraction
  - If missing: OCR disabled, no text extraction from images
  - Install: `pip install pytesseract`
  - Also requires: Tesseract OCR binary (`brew install tesseract` on macOS)

- **PyPDF2** - PDF text extraction
  - If missing: PDF analysis returns basic metadata only
  - Install: `pip install PyPDF2`

- **OpenCV (cv2)** - Video processing and advanced image analysis
  - If missing: Video processing disabled, damage detection disabled
  - Install: `pip install opencv-python`

### Other Optional Dependencies

- **cryptography** - Encryption (Fernet)
  - If missing: Uses no-op encryption in MVP mode
  - Install: `pip install cryptography`

- **anthropic** - Claude API client
  - If missing: LLM extraction will fail (but server starts)
  - Install: `pip install anthropic`

- **supabase** - Supabase client
  - If missing: Uses in-memory database automatically
  - Install: `pip install supabase`

- **celery** - Background task queue
  - If missing: Workers run synchronously (no error, just slower)
  - Install: `pip install celery redis`
  - **Note**: Server starts without Celery - workers process tasks immediately

## Minimal Installation

To start the server with absolute minimum dependencies:

```bash
pip install fastapi uvicorn python-dotenv pydantic pydantic-settings python-multipart
```

This will:
- ✅ Start the server
- ✅ Handle API requests
- ✅ Store data in memory
- ✅ Process incidents (without CV features)
- ❌ No image/PDF/video processing
- ❌ No OCR
- ❌ No LLM extraction (unless API key provided)

## Behavior When Dependencies Missing

### Image Upload
- **With Pillow**: Extracts dimensions, basic metadata
- **Without Pillow**: Returns error message, continues processing

### PDF Upload
- **With PyPDF2**: Extracts text, detects document types
- **Without PyPDF2**: Returns error message, continues processing

### Video Upload
- **With OpenCV**: Analyzes frames, extracts metadata
- **Without OpenCV**: Returns error message, continues processing

### OCR
- **With pytesseract**: Extracts text from images
- **Without pytesseract**: Skips OCR, continues with other analysis

## Error Messages

When dependencies are missing, you'll see warnings in the logs:

```
WARNING: PIL/Pillow not available - image processing disabled
WARNING: pytesseract not available - OCR disabled
WARNING: PyPDF2 not available - PDF processing disabled
WARNING: OpenCV not available - video processing disabled
```

These are **not errors** - the server continues to work, just with reduced functionality.

## Testing

### Test Without CV Dependencies

```bash
# Uninstall CV packages (if installed)
pip uninstall Pillow pytesseract PyPDF2 opencv-python -y

# Start server - should work fine
python run_mvp.py

# Test endpoint
curl -X POST "http://localhost:8000/incident" \
  -F "story_text=My car was hit"
```

### Test With CV Dependencies

```bash
# Install CV packages
pip install Pillow pytesseract PyPDF2 opencv-python

# Start server
python run_mvp.py

# Test with image upload
curl -X POST "http://localhost:8000/incident" \
  -F "story_text=See attached photo" \
  -F "files=@photo.jpg"
```

## Recommended Installation

For MVP testing with all features:

```bash
# Core dependencies
pip install fastapi uvicorn python-dotenv pydantic pydantic-settings python-multipart

# CV features (optional but recommended)
pip install Pillow pytesseract PyPDF2 opencv-python

# LLM (if you have API key)
pip install anthropic
```

## Summary

✅ **Server starts** without any CV dependencies  
✅ **API endpoints work** without CV dependencies  
✅ **Graceful degradation** - missing features return error messages but don't crash  
✅ **Easy to add** - install packages when needed  
✅ **No breaking changes** - existing code works with or without dependencies  

The backend is now truly MVP-ready with zero required external dependencies!
