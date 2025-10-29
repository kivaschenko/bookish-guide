"""
Pydantic models and schemas for API requests and responses.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, ConfigDict


# Enums for API responses
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class VideoGenerationStage(str, Enum):
    SCRIPT = "script"
    VOICE = "voice"
    BROLL = "broll"
    ASSEMBLY = "assembly"
    COMPLETE = "complete"


class VideoGenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class BRollCategory(str, Enum):
    NATURE = "nature"
    URBAN = "urban"
    PEOPLE = "people"
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    LIFESTYLE = "lifestyle"
    ABSTRACT = "abstract"
    OTHER = "other"


class BRollStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AVAILABLE = "available"
    ERROR = "error"


# Authentication schemas
class UserLogin(BaseModel):
    """User login request."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """User data response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Project schemas
class ProjectCreate(BaseModel):
    """Project creation request."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    input_text: Optional[str] = None
    language: str = Field(default="english", max_length=20)


class ProjectUpdate(BaseModel):
    """Project update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    input_text: Optional[str] = None
    language: Optional[str] = Field(None, max_length=20)
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    """Project data response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    input_text: Optional[str]
    language: str
    project_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    user_id: int


class ProjectListResponse(BaseModel):
    """Project list response."""

    projects: List[ProjectResponse]
    total: int


# Video generation schemas
class VideoGenerationResponse(BaseModel):
    """Video generation status response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    stage: VideoGenerationStage
    status: VideoGenerationStatus
    progress_percentage: int
    error_message: Optional[str]
    timeline_data: Optional[Dict[str, Any]]
    output_files: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class VideoGenerationCreate(BaseModel):
    """Video generation start request."""

    stage: VideoGenerationStage = VideoGenerationStage.SCRIPT
    force_restart: bool = False


# B-roll schemas
class BRollCreate(BaseModel):
    """B-roll creation/upload request."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="List of tags")
    category: BRollCategory = BRollCategory.OTHER
    is_public: bool = Field(
        default=True, description="Make B-roll public for all users"
    )


class BRollUpdate(BaseModel):
    """B-roll update request."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="List of tags")
    category: Optional[BRollCategory] = None
    is_public: Optional[bool] = None


class BRollResponse(BaseModel):
    """B-roll data response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str

    # Video metadata
    duration: Optional[float]
    width: Optional[int]
    height: Optional[int]
    fps: Optional[float]
    bitrate: Optional[int]

    # Content metadata
    title: str
    description: Optional[str]
    tags: Optional[List[str]] = None
    category: BRollCategory
    status: BRollStatus

    # AI metadata
    ai_description: Optional[str]
    ai_tags: Optional[List[str]] = None

    # User info
    uploaded_by: Optional[int]
    is_public: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime


class BRollListResponse(BaseModel):
    """B-roll list response."""

    brolls: List[BRollResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class BRollUploadResponse(BaseModel):
    """B-roll upload response."""

    success: bool
    message: str
    broll: Optional[BRollResponse] = None
    upload_id: Optional[str] = None


class BRollSearchRequest(BaseModel):
    """B-roll search request."""

    query: Optional[str] = Field(
        None, description="Search query for title, description, or tags"
    )
    category: Optional[BRollCategory] = None
    status: Optional[BRollStatus] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    duration_min: Optional[float] = Field(
        None, ge=0, description="Minimum duration in seconds"
    )
    duration_max: Optional[float] = Field(
        None, ge=0, description="Maximum duration in seconds"
    )
    uploaded_by_me: Optional[bool] = Field(
        None, description="Filter by current user uploads"
    )


# Existing timeline schemas (keeping for backward compatibility)


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


class BrollClip(BaseModel):
    """Individual B-roll clip within a rush."""

    video: str = Field(..., description="Name of the B-roll video file")
    start: float = Field(..., description="Start time within the video")
    duration: float = Field(..., description="Duration of the clip")
    score: float = Field(..., description="Matching score for the clip")


class Rush(BaseModel):
    """Individual rush/segment with associated B-roll clips."""

    duration: float = Field(..., description="Duration of the rush in seconds")
    brolls: List[BrollClip] = Field(
        ..., description="List of B-roll clips for this rush"
    )
    message: str = Field(..., description="Descriptive message about the rush")


class TimelineResponse(BaseModel):
    """Complete timeline response structure matching broll_timing.json format."""

    rushes: Dict[str, Rush] = Field(
        ..., description="Dictionary of rushes keyed by rush ID"
    )


class TimelineUpdateRequest(BaseModel):
    """Request model for updating timeline data."""

    timeline_data: Dict[str, Any] = Field(..., description="Updated timeline data")


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
