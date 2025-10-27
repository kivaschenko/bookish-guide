#!/usr/bin/env python3
"""
FastAPI server for the premontage system.
Provides a modern web interface for B-roll timeline editing and synchronization.

Based on the legacy server but rebuilt with FastAPI for better performance,
WebSocket support, and modern API architecture.
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Request,
)
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasicCredentials
import uvicorn

from config.settings import Settings, get_settings
from auth.middleware import verify_credentials
from routes import api
from websocket.handler import WebSocketManager


# Global WebSocket manager
websocket_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    settings = get_settings()
    logging.info("🚀 Starting Premontage FastAPI server")
    logging.info(f"📁 Project path: {settings.paths.projects}")
    logging.info(f"🎬 B-roll path: {settings.paths.b_roll}")

    # Create necessary directories
    Path(settings.paths.b_roll).mkdir(exist_ok=True)
    Path(settings.paths.projects).mkdir(exist_ok=True)
    ressources_dir = Path(settings.paths.b_roll) / "ressources"
    ressources_dir.mkdir(exist_ok=True)

    yield

    # Shutdown
    logging.info("🛑 Shutting down Premontage FastAPI server")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="StoryForge Premontage API",
        description="FastAPI backend for video premontage system with timeline editing and B-roll synchronization",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api.router, prefix="/api", tags=["api"])

    return app


app = create_app()


@app.get("/", response_class=HTMLResponse)
async def serve_interface(
    request: Request,
    settings: Settings = Depends(get_settings),
    credentials: Optional[HTTPBasicCredentials] = Depends(verify_credentials),
):
    """Serve the main HTML interface."""
    # Determine project name from current temp path
    project_name = "unknown"
    temp_path = Path(settings.paths.temp)
    if temp_path.name == "temp" and temp_path.parent.name != "temp":
        project_name = temp_path.parent.name

    # Read the HTML interface template
    interface_path = Path(__file__).parent / "static" / "interface.html"

    if not interface_path.exists():
        # Fallback to legacy interface if new one doesn't exist yet
        legacy_interface = Path(__file__).parent / "legacy_server" / "interface.html"
        if legacy_interface.exists():
            interface_path = legacy_interface
        else:
            raise HTTPException(status_code=404, detail="Interface template not found")

    with open(interface_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Replace template variables
    html_content = html_content.replace("{{PROJECT_NAME}}", project_name)

    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time communication."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            # Echo back or process the message
            await websocket_manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "premontage-api"}


# Serve static files (B-roll videos, images, audio files)
@app.get("/b-roll/{file_path:path}")
async def serve_broll_file(
    file_path: str,
    settings: Settings = Depends(get_settings),
    credentials: Optional[HTTPBasicCredentials] = Depends(verify_credentials),
):
    """Serve B-roll files for preview."""
    full_path = Path(settings.paths.b_roll) / file_path

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    suffix = full_path.suffix.lower()
    if suffix in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif suffix == ".png":
        media_type = "image/png"
    elif suffix in [".mp4", ".mov"]:
        media_type = "video/mp4"
    elif suffix in [".mp3", ".wav"]:
        media_type = "audio/mpeg"
    else:
        media_type = "application/octet-stream"

    return FileResponse(full_path, media_type=media_type)


@app.get("/projects/{file_path:path}")
async def serve_project_file(
    file_path: str,
    settings: Settings = Depends(get_settings),
    credentials: Optional[HTTPBasicCredentials] = Depends(verify_credentials),
):
    """Serve project files for preview."""
    full_path = Path(settings.paths.projects) / file_path

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    suffix = full_path.suffix.lower()
    if suffix in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif suffix == ".png":
        media_type = "image/png"
    elif suffix in [".mp4", ".mov"]:
        media_type = "video/mp4"
    elif suffix in [".mp3", ".wav"]:
        media_type = "audio/mpeg"
    elif suffix == ".txt":
        media_type = "text/plain"
    elif suffix == ".json":
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"

    return FileResponse(full_path, media_type=media_type)


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True,
        log_level="info",
    )
