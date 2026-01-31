#!/usr/bin/env python3
"""
MVP startup script for Assura backend.
Runs the API server with in-memory database, no external dependencies required.
No encryption, no Supabase, no Redis needed.
"""

import uvicorn
import sys
import os

# Set MVP mode environment variables
os.environ["USE_MEMORY_DB"] = "true"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "INFO"

# Set dummy encryption key (won't be used in MVP mode)
os.environ["ENCRYPTION_KEY"] = "dummy-encryption-key-32-bytes-long!!"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("Assura Backend - Mode MVP")
    print("=" * 60)
    print("✓ Base de données en mémoire (pas de Supabase)")
    print("✓ Chiffrement désactivé (pas de clé Fernet)")
    print("✓ Workers synchrones (pas de Redis/Celery)")
    print("✓ Authentification simulée (tout token accepté)")
    print("")
    print("API disponible : http://0.0.0.0:5000")
    print("Documentation API : http://0.0.0.0:5000/docs")
    print("=" * 60)
    print()
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=5000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
