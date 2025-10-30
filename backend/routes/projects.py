"""
Project management API routes with user isolation.
"""

from pathlib import Path
from typing import List, Dict, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from models.connection import get_db
from models.database import User, Project, VideoGeneration
from models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    VideoGenerationResponse,
    VideoGenerationCreate,
)
from auth.dependencies import get_current_active_user
from config.settings import get_settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


def get_user_project_path(user_id: int, project_name: str) -> Path:
    """Get user-specific project path."""
    settings = get_settings()
    return Path(settings.paths.projects) / f"user_{user_id}" / project_name


def get_user_temp_path(user_id: int, project_name: str) -> Path:
    """Get user-specific temp path."""
    settings = get_settings()
    return Path(settings.paths.temp) / f"user_{user_id}" / project_name


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectListResponse:
    """List user's projects with pagination and filtering."""

    # Build query
    query = select(Project).where(Project.user_id == current_user.id)

    if status_filter:
        query = query.where(Project.status == status_filter)

    # Add ordering and pagination
    query = query.order_by(desc(Project.updated_at)).offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    projects = result.scalars().all()

    # Get total count
    count_query = select(Project).where(Project.user_id == current_user.id)
    if status_filter:
        count_query = count_query.where(Project.status == status_filter)

    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p) for p in projects], total=total
    )


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new project for the current user."""
    logger.info(
        f"User {current_user.id} is creating a new project: {project_data.name}"
    )

    # Check if project name already exists for this user
    result = await db.execute(
        select(Project).where(
            and_(Project.user_id == current_user.id, Project.name == project_data.name)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists",
        )

    # Create project directories
    project_path = get_user_project_path(current_user.id, project_data.name)
    temp_path = get_user_temp_path(current_user.id, project_data.name)

    # Create directory structure
    language_dir = project_path / project_data.language
    audio_dir = language_dir / "audio"

    try:
        project_path.mkdir(parents=True, exist_ok=True)
        language_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)
        temp_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project directories: {e}",
        )

    # Create project record
    project = Project(
        name=project_data.name,
        description=project_data.description,
        user_id=current_user.id,
        input_text=project_data.input_text,
        language=project_data.language,
        project_path=str(project_path),
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"User {current_user.id} created a new project: {project_data.name}")

    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Get a specific project."""

    result = await db.execute(
        select(Project).where(
            and_(Project.id == project_id, Project.user_id == current_user.id)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update a project."""

    result = await db.execute(
        select(Project).where(
            and_(Project.id == project_id, Project.user_id == current_user.id)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Delete a project and its files."""
    logger.info(f"User {current_user.id} is deleting project ID: {project_id}")
    result = await db.execute(
        select(Project).where(
            and_(Project.id == project_id, Project.user_id == current_user.id)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Delete project files
    if project.project_path:
        project_path = Path(project.project_path)
        if project_path.exists():
            import shutil

            try:
                shutil.rmtree(project_path)
            except Exception as e:
                # Log error but don't fail the deletion
                print(f"Warning: Failed to delete project files: {e}")

    # Delete temp files
    temp_path = get_user_temp_path(current_user.id, project.name)
    if temp_path.exists():
        import shutil

        try:
            shutil.rmtree(temp_path)
        except Exception as e:
            print(f"Warning: Failed to delete temp files: {e}")

    # Delete from database
    await db.delete(project)
    await db.commit()

    logger.info(f"User {current_user.id} deleted project ID: {project_id}")
    return {"message": "Project deleted successfully"}


@router.get(
    "/{project_id}/video-generations", response_model=List[VideoGenerationResponse]
)
async def list_video_generations(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[VideoGenerationResponse]:
    """List video generations for a project."""
    logger.info(
        f"User {current_user.id} is listing video generations for project ID: {project_id}"
    )
    # Verify project ownership
    result = await db.execute(
        select(Project).where(
            and_(Project.id == project_id, Project.user_id == current_user.id)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Get video generations
    result = await db.execute(
        select(VideoGeneration)
        .where(VideoGeneration.project_id == project_id)
        .order_by(desc(VideoGeneration.created_at))
    )
    generations = result.scalars().all()

    return [VideoGenerationResponse.model_validate(gen) for gen in generations]


@router.post("/{project_id}/video-generations", response_model=VideoGenerationResponse)
async def create_video_generation(
    project_id: int,
    generation_data: VideoGenerationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VideoGenerationResponse:
    """Start video generation for a project."""
    logger.info(
        f"User {current_user.id} is starting video generation for project ID: {project_id}"
    )
    # Verify project ownership
    result = await db.execute(
        select(Project).where(
            and_(Project.id == project_id, Project.user_id == current_user.id)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Check if input text is provided
    if not project.input_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have input text to start video generation",
        )

    # Create video generation record
    generation = VideoGeneration(
        project_id=project_id,
        stage=generation_data.stage,
    )

    db.add(generation)
    await db.commit()
    await db.refresh(generation)
    logger.info(
        f"User {current_user.id} started video generation ID: {generation.id} for project ID: {project_id}"
    )
    # TODO: Here you would trigger the actual video generation process
    # For now, we just return the created record

    return VideoGenerationResponse.model_validate(generation)
