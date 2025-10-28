"""
API routes for the premontage system.
Handles timeline data, file uploads, and other REST endpoints.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBasicCredentials

from config.settings import Settings, get_settings
from auth.middleware import verify_credentials
from models.schemas import TimelineUpdateRequest, UploadResponse, TimelineResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline_data(
    settings: Settings = Depends(get_settings),
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    """Get the current timeline data from broll_timing.json."""
    broll_timing_file = Path(settings.paths.temp) / "broll_timing.json"
    logger.info(f"Reading timeline data from {broll_timing_file}")

    if not broll_timing_file.exists():
        raise HTTPException(
            status_code=404,
            detail="broll_timing.json not found. Run the B-roll processing first.",
        )

    try:
        with open(broll_timing_file, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)
            logger.info(f"Timeline data: {timeline_data}")
        return timeline_data
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"Invalid JSON in timeline file: {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading timeline file: {e}")


@router.post("/timeline", response_model=Dict[str, str])
async def update_timeline_data(
    request: TimelineUpdateRequest,
    settings: Settings = Depends(get_settings),
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    """Update the timeline data in broll_timing.json."""
    broll_timing_file = Path(settings.paths.temp) / "broll_timing.json"

    try:
        with open(broll_timing_file, "w", encoding="utf-8") as f:
            json.dump(request.timeline_data, f, indent=2, ensure_ascii=False)

        return {"success": "true", "message": "Timeline updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating timeline: {e}")


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    broll_index: int = Form(...),
    settings: Settings = Depends(get_settings),
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    """Upload an image to overlay on a B-roll video."""
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
        )

    # Create ressources directory
    ressources_dir = Path(settings.paths.b_roll) / "ressources"
    ressources_dir.mkdir(exist_ok=True)

    # Generate unique filename
    timestamp = int(time.time())
    new_filename = f"uploaded_{timestamp}_{broll_index}{file_ext}"
    save_path = ressources_dir / new_filename

    try:
        # Save uploaded file
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Update timeline data
        broll_timing_file = Path(settings.paths.temp) / "broll_timing.json"

        if not broll_timing_file.exists():
            raise HTTPException(status_code=404, detail="broll_timing.json not found")

        with open(broll_timing_file, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)

        if not (0 <= broll_index < len(timeline_data)):
            raise HTTPException(status_code=400, detail="Invalid B-roll index")

        # Add image overlay to B-roll item
        timeline_data[broll_index]["image"] = f"ressources/{new_filename}"

        with open(broll_timing_file, "w", encoding="utf-8") as f:
            json.dump(timeline_data, f, indent=2, ensure_ascii=False)

        return UploadResponse(
            success=True,
            message=f"Image uploaded and added to B-roll {broll_index}",
            file_path=f"ressources/{new_filename}",
            file_size=len(content),
        )

    except Exception as e:
        # Clean up file if something went wrong
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error uploading file: {e}")


@router.get("/project-info")
async def get_project_info(
    settings: Settings = Depends(get_settings),
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    """Get information about the current project."""
    temp_path = Path(settings.paths.temp)
    project_name = "unknown"

    if temp_path.name == "temp" and temp_path.parent.name != "temp":
        project_name = temp_path.parent.name

    # Check if required files exist
    broll_timing_exists = (temp_path / "broll_timing.json").exists()

    return {
        "project_name": project_name,
        "temp_path": str(temp_path),
        "broll_timing_exists": broll_timing_exists,
        "b_roll_path": settings.paths.b_roll,
        "projects_path": settings.paths.projects,
    }


@router.get("/status")
async def get_system_status(
    settings: Settings = Depends(get_settings),
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    """Get system status and health information."""
    # Check if essential directories exist
    b_roll_exists = Path(settings.paths.b_roll).exists()
    projects_exists = Path(settings.paths.projects).exists()
    temp_exists = Path(settings.paths.temp).exists()

    # Check if timeline file exists
    broll_timing_file = Path(settings.paths.temp) / "broll_timing.json"
    timeline_exists = broll_timing_file.exists()

    return {
        "status": "operational",
        "directories": {
            "b_roll": b_roll_exists,
            "projects": projects_exists,
            "temp": temp_exists,
        },
        "files": {"timeline": timeline_exists},
        "authentication_enabled": settings.authentication.enabled,
    }


@router.delete("/upload/{filename}")
async def delete_uploaded_file(
    filename: str,
    settings: Settings = Depends(get_settings),
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    """Delete an uploaded overlay image."""
    ressources_dir = Path(settings.paths.b_roll) / "ressources"
    file_path = ressources_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Security check: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        file_path.unlink()
        return {"success": True, "message": f"File {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {e}")
