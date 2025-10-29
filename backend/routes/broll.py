"""
B-roll management API routes.
"""

import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from auth.dependencies import get_current_user
from config.settings import get_settings
from models.connection import get_db
from models.database import BRoll, BRollCategory, BRollStatus
from models.schemas import (
    BRollUpdate,
    BRollResponse,
    BRollListResponse,
    BRollUploadResponse,
    UserResponse,
    BRollCategory as SchemaBRollCategory,
    BRollStatus as SchemaBRollStatus,
)
from services.broll_service import BRollService

router = APIRouter(prefix="/api/broll", tags=["B-roll"])


def broll_to_response(broll: BRoll) -> BRollResponse:
    """Convert BRoll model to BRollResponse schema."""
    # Parse JSON strings back to lists
    tags = []
    ai_tags = []

    if broll.tags:
        try:
            tags = json.loads(broll.tags) if isinstance(broll.tags, str) else broll.tags
        except Exception:
            tags = []

    if broll.ai_tags:
        try:
            ai_tags = (
                json.loads(broll.ai_tags)
                if isinstance(broll.ai_tags, str)
                else broll.ai_tags
            )
        except Exception:
            ai_tags = []

    return BRollResponse(
        id=broll.id,
        filename=broll.filename,
        original_filename=broll.original_filename,
        file_path=broll.file_path,
        file_size=broll.file_size,
        mime_type=broll.mime_type,
        duration=broll.duration,
        width=broll.width,
        height=broll.height,
        fps=broll.fps,
        bitrate=broll.bitrate,
        title=broll.title,
        description=broll.description,
        tags=tags,
        category=SchemaBRollCategory(broll.category.value),  # Convert enum
        status=SchemaBRollStatus(broll.status.value),  # Convert enum
        ai_description=broll.ai_description,
        ai_tags=ai_tags,
        uploaded_by=broll.uploaded_by,
        is_public=broll.is_public,
        created_at=broll.created_at,
        updated_at=broll.updated_at,
    )


@router.post("/upload", response_model=BRollUploadResponse)
async def upload_broll(
    title: str,
    description: Optional[str] = None,
    category: Optional[BRollCategory] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new B-roll file."""
    broll_service = BRollService()

    try:
        # Save the file
        filename, file_path, file_size = await broll_service.save_upload_file(file)

        # Get file info
        file_info = broll_service.get_file_info(filename)

        # Extract metadata if it's a video
        metadata = None
        ai_tags = None
        if broll_service._is_video_file(filename):
            try:
                metadata_result = await broll_service.extract_video_metadata(filename)
                if metadata_result and metadata_result.get("analysis"):
                    metadata = metadata_result
                    # Extract keywords from analysis if available
                    analysis = metadata_result.get("analysis", "")
                    if "Keywords:" in analysis:
                        keywords_section = analysis.split("Keywords:")[-1].strip()
                        keywords = [
                            k.strip() for k in keywords_section.split(",") if k.strip()
                        ]
                        ai_tags = keywords[:20]  # Limit to 20 tags
            except Exception as e:
                print(f"Warning: Could not extract metadata for {filename}: {e}")

        # Parse user tags
        user_tags = []
        if tags:
            user_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Combine user tags and AI tags
        all_tags = user_tags + (ai_tags or [])

        # Create database record
        db_broll = BRoll(
            title=title,
            description=description or "",
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file_info.get("mime_type", "application/octet-stream")
            if file_info
            else "application/octet-stream",
            category=category or BRollCategory.OTHER,
            tags=json.dumps(all_tags) if all_tags else None,
            ai_description=metadata.get("analysis") if metadata else None,
            ai_tags=json.dumps(ai_tags) if ai_tags else None,
            uploaded_by=current_user.id,
            status=BRollStatus.AVAILABLE,
        )

        db.add(db_broll)
        await db.commit()
        await db.refresh(db_broll)

        broll_response = broll_to_response(db_broll)

        return BRollUploadResponse(
            success=True, message="File uploaded successfully", broll=broll_response
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if database operation failed
        if "filename" in locals():
            broll_service.delete_file(filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get("/", response_model=BRollListResponse)
async def list_broll(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[BRollCategory] = None,
    status: Optional[BRollStatus] = None,
    search: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List B-roll files with optional filtering."""
    # Build query - get user's files or public files
    query = select(BRoll).where(
        or_(BRoll.uploaded_by == current_user.id, BRoll.is_public.is_(True))
    )

    # Apply filters
    if category:
        query = query.where(BRoll.category == category)

    if status:
        query = query.where(BRoll.status == status)
    else:
        # Default to available only
        query = query.where(BRoll.status == BRollStatus.AVAILABLE)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                BRoll.title.ilike(search_term),
                BRoll.description.ilike(search_term),
                BRoll.filename.ilike(search_term),
            )
        )

    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        for tag in tag_list:
            # Search in JSON string
            query = query.where(BRoll.tags.like(f'%"{tag}"%'))

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.fetchall())

    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Apply pagination
    query = query.offset(offset).limit(per_page).order_by(BRoll.created_at.desc())

    result = await db.execute(query)
    broll_items = result.scalars().all()

    # Convert to response format
    brolls = [broll_to_response(item) for item in broll_items]

    return BRollListResponse(
        brolls=brolls,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{broll_id}", response_model=BRollResponse)
async def get_broll(
    broll_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific B-roll item."""
    query = select(BRoll).where(
        and_(
            BRoll.id == broll_id,
            or_(BRoll.uploaded_by == current_user.id, BRoll.is_public.is_(True)),
        )
    )

    result = await db.execute(query)
    broll = result.scalar_one_or_none()

    if not broll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="B-roll item not found"
        )

    return broll_to_response(broll)


@router.put("/{broll_id}", response_model=BRollResponse)
async def update_broll(
    broll_id: int,
    broll_update: BRollUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update B-roll item metadata."""
    query = select(BRoll).where(
        and_(
            BRoll.id == broll_id,
            BRoll.uploaded_by == current_user.id,  # Only owner can update
        )
    )

    result = await db.execute(query)
    broll = result.scalar_one_or_none()

    if not broll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="B-roll item not found or not owned by user",
        )

    # Update fields
    update_data = broll_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tags" and value is not None:
            setattr(broll, field, json.dumps(value))
        else:
            setattr(broll, field, value)

    await db.commit()
    await db.refresh(broll)

    return broll_to_response(broll)


@router.delete("/{broll_id}")
async def delete_broll(
    broll_id: int,
    permanent: bool = Query(
        False, description="Permanently delete file instead of changing status"
    ),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete B-roll item."""
    broll_service = BRollService()

    query = select(BRoll).where(
        and_(
            BRoll.id == broll_id,
            BRoll.uploaded_by == current_user.id,  # Only owner can delete
        )
    )

    result = await db.execute(query)
    broll = result.scalar_one_or_none()

    if not broll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="B-roll item not found or not owned by user",
        )

    if permanent:
        # Delete file from filesystem
        broll_service.delete_file(broll.filename)

        # Delete from database
        await db.delete(broll)
        await db.commit()

        return {"message": "B-roll item permanently deleted"}
    else:
        # Change status to ERROR (closest to soft delete)
        broll.status = BRollStatus.ERROR
        await db.commit()

        return {"message": "B-roll item status changed to error"}


@router.get("/files/{filename}")
async def get_file(
    filename: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve B-roll file."""
    # Verify user has access to this file
    query = select(BRoll).where(
        and_(
            BRoll.filename == filename,
            or_(BRoll.uploaded_by == current_user.id, BRoll.is_public.is_(True)),
            BRoll.status == BRollStatus.AVAILABLE,
        )
    )

    result = await db.execute(query)
    broll = result.scalar_one_or_none()

    if not broll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied",
        )

    # Serve file
    settings = get_settings()
    file_path = Path(settings.paths.b_roll) / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk"
        )

    return FileResponse(path=file_path, filename=filename, media_type=broll.mime_type)


@router.get("/stats/storage")
async def get_storage_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get storage statistics for current user."""
    broll_service = BRollService()

    # Get user's file count and sizes from database
    query = select(BRoll).where(
        and_(
            BRoll.uploaded_by == current_user.id, BRoll.status == BRollStatus.AVAILABLE
        )
    )

    result = await db.execute(query)
    user_files = result.scalars().all()

    total_files = len(user_files)
    total_size = sum(f.file_size for f in user_files)
    video_files = sum(1 for f in user_files if broll_service._is_video_file(f.filename))
    image_files = sum(1 for f in user_files if broll_service._is_image_file(f.filename))

    # Get overall system stats
    system_stats = broll_service.get_storage_stats()

    return {
        "user_stats": {
            "total_files": total_files,
            "video_files": video_files,
            "image_files": image_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        },
        "system_stats": system_stats,
    }
