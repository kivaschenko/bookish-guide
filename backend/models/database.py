"""
Database models for multi-user StoryForge system.
Defines User, Project, VideoGeneration, and UserSession models.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    JSON,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class UserRole(enum.Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


class ProjectStatus(enum.Enum):
    """Project status enumeration."""

    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class VideoGenerationStage(enum.Enum):
    """Video generation stage enumeration."""

    SCRIPT = "script"
    VOICE = "voice"
    BROLL = "broll"
    ASSEMBLY = "assembly"
    COMPLETE = "complete"


class VideoGenerationStatus(enum.Enum):
    """Video generation status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Project(Base):
    """Project model for user video projects."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False
    )
    input_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="english", nullable=False)
    project_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # File system path
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    video_generations: Mapped[List["VideoGeneration"]] = relationship(
        "VideoGeneration", back_populates="project", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_project_user_created", "user_id", "created_at"),
        Index("idx_project_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', user_id={self.user_id}, status='{self.status.value}')>"


class VideoGeneration(Base):
    """Video generation tracking model."""

    __tablename__ = "video_generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    stage: Mapped[VideoGenerationStage] = mapped_column(
        Enum(VideoGenerationStage), default=VideoGenerationStage.SCRIPT, nullable=False
    )
    status: Mapped[VideoGenerationStatus] = mapped_column(
        Enum(VideoGenerationStatus),
        default=VideoGenerationStatus.PENDING,
        nullable=False,
    )
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timeline_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # B-roll timeline
    output_files: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Generated files info
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="video_generations"
    )

    # Indexes
    __table_args__ = (
        Index("idx_video_generation_project_created", "project_id", "created_at"),
        Index("idx_video_generation_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<VideoGeneration(id={self.id}, project_id={self.project_id}, stage='{self.stage.value}', status='{self.status.value}')>"


class UserSession(Base):
    """User session tracking for JWT token management."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    token_jti: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )  # JWT ID
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("idx_session_user_expires", "user_id", "expires_at"),
        Index("idx_session_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at='{self.expires_at}')>"
