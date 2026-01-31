"""
Main FastAPI application for Assura backend.
Entry point for the API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import incidents
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Assura API",
    description="Assistant Invisible pour l'Assurance - Backend",
    version="0.1.0"
)

# CORS middleware (configure for your frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents.router)


@app.get("/")
async def root():
    """Point de contrôle de santé."""
    return {
        "statut": "opérationnel",
        "service": "Assura API",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Contrôle de santé détaillé."""
    return {
        "statut": "opérationnel",
        "environnement": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
