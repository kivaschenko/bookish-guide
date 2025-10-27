"""
Pydantic models and schemas for API requests and responses.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class TimelineItem(BaseModel):
    """Individual timeline item representing a B-roll segment."""

    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    broll_path: str = Field(..., description="Path to the B-roll video file")
    bullet_point: str = Field(..., description="Associated bullet point text")
    similarity_score: Optional[float] = Field(
        None, description="Similarity score for matching"
    )
    image: Optional[str] = Field(None, description="Path to overlay image")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TimelineData(BaseModel):
    """Complete timeline data structure."""

    items: List[TimelineItem] = Field(..., description="List of timeline items")
    total_duration: Optional[float] = Field(None, description="Total timeline duration")
    project_name: Optional[str] = Field(None, description="Project name")


class TimelineUpdateRequest(BaseModel):
    """Request model for updating timeline data."""

    timeline_data: List[Dict[str, Any]] = Field(
        ..., description="Updated timeline data"
    )


class UploadResponse(BaseModel):
    """Response model for file upload operations."""

    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message")
    file_path: Optional[str] = Field(None, description="Path to the uploaded file")
    file_size: Optional[int] = Field(None, description="Size of uploaded file in bytes")


class ProjectInfo(BaseModel):
    """Project information response."""

    project_name: str = Field(..., description="Name of the current project")
    temp_path: str = Field(..., description="Path to temporary files")
    broll_timing_exists: bool = Field(
        ..., description="Whether broll_timing.json exists"
    )
    b_roll_path: str = Field(..., description="Path to B-roll directory")
    projects_path: str = Field(..., description="Path to projects directory")


class SystemStatus(BaseModel):
    """System status and health information."""

    status: str = Field(..., description="Overall system status")
    directories: Dict[str, bool] = Field(..., description="Directory existence status")
    files: Dict[str, bool] = Field(..., description="Important file existence status")
    authentication_enabled: bool = Field(
        ..., description="Whether authentication is enabled"
    )
    connected_clients: Optional[int] = Field(
        None, description="Number of connected WebSocket clients"
    )


class LogMessage(BaseModel):
    """Log message structure for WebSocket communication."""

    type: str = Field(default="log", description="Message type")
    level: str = Field(..., description="Log level (info, warning, error, etc.)")
    message: str = Field(..., description="Log message content")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the log"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional log details"
    )


class ProgressUpdate(BaseModel):
    """Progress update structure for WebSocket communication."""

    type: str = Field(default="progress", description="Message type")
    task: str = Field(..., description="Name of the task being tracked")
    progress: float = Field(
        ..., ge=0.0, le=1.0, description="Progress as a float between 0.0 and 1.0"
    )
    status: str = Field(..., description="Current status of the task")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the update"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional progress details"
    )


class SystemNotification(BaseModel):
    """System notification structure for WebSocket communication."""

    type: str = Field(default="notification", description="Message type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    notification_type: str = Field(
        default="info",
        description="Type of notification (info, success, warning, error)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the notification"
    )


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""

    type: str = Field(..., description="Type of message")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Message timestamp"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")


class ClientMessage(BaseModel):
    """Client message structure for incoming WebSocket messages."""

    type: str = Field(..., description="Message type from client")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data from client")


class ErrorResponse(BaseModel):
    """Error response structure."""

    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )


class SuccessResponse(BaseModel):
    """Success response structure."""

    success: bool = Field(default=True, description="Always true for success responses")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


# File operation models
class FileInfo(BaseModel):
    """File information structure."""

    filename: str = Field(..., description="Name of the file")
    path: str = Field(..., description="Full path to the file")
    size: int = Field(..., description="File size in bytes")
    modified: datetime = Field(..., description="Last modified timestamp")
    mime_type: str = Field(..., description="MIME type of the file")


class DeleteFileRequest(BaseModel):
    """Request to delete a file."""

    filename: str = Field(..., description="Name of the file to delete")
    confirm: bool = Field(default=False, description="Confirmation flag")


# Configuration models
class AuthenticationSettings(BaseModel):
    """Authentication configuration."""

    enabled: bool = Field(
        default=False, description="Whether authentication is enabled"
    )
    username: str = Field(default="admin", description="Username for basic auth")
    password: str = Field(default="admin", description="Password for basic auth")


class ServerSettings(BaseModel):
    """Server configuration."""

    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=47393, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload in development")


class PathSettings(BaseModel):
    """Path configuration with absolute paths."""

    projects: str = Field(
        default="./projects", description="Absolute path to projects directory"
    )
    b_roll: str = Field(
        default="./b-roll", description="Absolute path to B-roll directory"
    )
    temp: str = Field(default="./temp", description="Absolute path to temporary files")


class Settings(BaseModel):
    """Complete application settings."""

    authentication: AuthenticationSettings = Field(
        default_factory=AuthenticationSettings
    )
    server: ServerSettings = Field(default_factory=ServerSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
