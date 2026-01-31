# MVP Mode - No-Op Encryption

## Overview

In MVP mode, the encryption service uses **no-op encryption** - data is stored and retrieved unchanged. This eliminates the need for a valid Fernet encryption key during testing.

## How It Works

### Automatic Detection

The encryption service automatically detects MVP mode by checking `settings.use_memory_db`:

```python
# In app/services/encryption_service.py
_use_mvp_encryption = settings.use_memory_db
```

### No-Op Functions

When in MVP mode:
- `encrypt_field(value)` → Returns `value` unchanged
- `decrypt_field(value)` → Returns `value` unchanged
- `encrypt_dict_fields(data, fields)` → Returns `data` with fields unchanged
- `decrypt_dict_fields(data, fields)` → Returns `data` with fields unchanged

### Fernet Initialization

Fernet encryption is only initialized when:
1. `use_memory_db = False` (not in MVP mode)
2. Valid encryption key is available
3. `cryptography` package is installed

If any of these fail, the service automatically falls back to no-op mode.

## Testing

### Verify No-Op Encryption

```bash
python test_encryption_mvp.py
```

This will verify that:
- Encryption returns data unchanged
- Decryption returns data unchanged
- Dictionary encryption/decryption works correctly

### Manual Test

```python
import os
os.environ["USE_MEMORY_DB"] = "true"

from app.services.encryption_service import encrypt_field, decrypt_field

# In MVP mode, these are no-ops
original = "sensitive-data"
encrypted = encrypt_field(original)  # Returns "sensitive-data"
decrypted = decrypt_field(encrypted)  # Returns "sensitive-data"

assert encrypted == original  # True in MVP mode
assert decrypted == original   # True in MVP mode
```

## Benefits

✅ **No encryption key required** - Works without valid Fernet key  
✅ **No cryptography dependency** - Works even if package not installed  
✅ **Simpler testing** - Data stored as-is, easier to debug  
✅ **Faster** - No encryption/decryption overhead  
✅ **Automatic fallback** - If Fernet fails, uses no-op mode  

## Security Note

⚠️ **Important**: No-op encryption means data is stored as **plain text** in MVP mode. This is intentional for testing but should **never** be used in production.

## Switching to Real Encryption

When ready for production:

1. Set `USE_MEMORY_DB=false` in `.env`
2. Generate a real encryption key:
   ```bash
   python scripts/generate_key.py
   ```
3. Add to `.env`:
   ```
   ENCRYPTION_KEY=your-generated-key-here
   ```
4. Restart the server

The encryption service will automatically switch to real Fernet encryption.

## Code Changes

### Modified Files

- `app/services/encryption_service.py` - Added MVP mode detection and no-op functions
- `run_mvp.py` - Sets MVP mode environment variable
- `app/config.py` - Updated comments to reflect optional encryption

### No Changes Required

- `app/routes/incidents.py` - Works with both modes automatically
- `app/workers/incident_worker.py` - Works with both modes automatically
- All other services - No changes needed

## Verification

All endpoints work correctly with no-op encryption:

```bash
# Start server
python run_mvp.py

# Create incident (no encryption key needed)
curl -X POST "http://localhost:8000/incident" \
  -F "story_text=My car was hit"

# Get incident (data retrieved as-is)
curl "http://localhost:8000/incident/INCIDENT_ID"
```

The backend is now fully MVP-testable without any encryption requirements!
