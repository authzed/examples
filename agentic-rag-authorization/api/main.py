"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routes import router
from .config import get_api_config

# Create FastAPI app
app = FastAPI(
    title="Agentic RAG Authorization API",
    version="1.0.0",
    description="API for demonstrating fine-grained authorization in RAG systems",
)

# Get configuration
config = get_api_config()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=config.api_prefix)

# Serve frontend static files
ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
if os.path.exists(ui_path):
    # Serve index.html at root
    @app.get("/")
    async def read_root():
        """Serve the frontend UI."""
        index_path = os.path.join(ui_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend UI not found. Please create ui/index.html"}

    # Mount static files for any other assets
    app.mount("/static", StaticFiles(directory=ui_path), name="static")
else:
    @app.get("/")
    async def read_root():
        """Root endpoint when UI not available."""
        return {
            "message": "Agentic RAG API",
            "docs": "/docs",
            "api": "/api",
        }
