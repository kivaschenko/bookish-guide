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
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


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
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
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
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
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
        return f"<Project(id={self.id}, name='{self.name}', user_id={self.user_id}, status='{self.status}')>"


class VideoGeneration(Base):
    """Video generation tracking model."""

    __tablename__ = "video_generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(20), default="script", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
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
        return f"<VideoGeneration(id={self.id}, project_id={self.project_id}, stage='{self.stage}', status='{self.status}')>"


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


class BRoll(Base):
    """B-roll video model for managing video assets."""

    __tablename__ = "brolls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False
    )  # Relative to b-roll directory
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Size in bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Video metadata
    duration: Mapped[Optional[float]] = mapped_column(
        nullable=True
    )  # Duration in seconds
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(nullable=True)  # Frames per second
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Content metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array as string
    category: Mapped[str] = mapped_column(String(20), default="other", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    # AI-generated metadata
    ai_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_tags: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array as string
    embedding_vector: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON array as string

    # User association (optional - can be null for shared B-roll)
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Public B-roll accessible to all users

    # Timestamps
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
    uploader: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[uploaded_by]
    )

    # Indexes
    __table_args__ = (
        Index("idx_broll_category", "category"),
        Index("idx_broll_status", "status"),
        Index("idx_broll_public", "is_public"),
        Index("idx_broll_uploader", "uploaded_by"),
        Index("idx_broll_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<BRoll(id={self.id}, filename='{self.filename}', title='{self.title}', category='{self.category}')>"
