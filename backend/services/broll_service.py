"""
B-roll service for file handling and metadata extraction.
"""

import uuid
import mimetypes
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import aiofiles
from fastapi import UploadFile, HTTPException

from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BRollService:
    """Service for handling B-roll file operations."""

    def __init__(self):
        self.settings = get_settings()
        self.broll_dir = Path(self.settings.paths.b_roll)
        self.broll_dir.mkdir(exist_ok=True)
        logger.info(f"B-roll directory set to: {self.broll_dir}")

    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()

    def _is_video_file(self, filename: str) -> bool:
        """Check if file is a supported video format."""
        video_extensions = {
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
            ".m4v",
            ".3gp",
            ".flv",
        }
        return self._get_file_extension(filename) in video_extensions

    def _is_image_file(self, filename: str) -> bool:
        """Check if file is a supported image format."""
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
        return self._get_file_extension(filename) in image_extensions

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename to avoid conflicts."""
        ext = self._get_file_extension(original_filename)
        unique_id = str(uuid.uuid4())[:8]
        base_name = Path(original_filename).stem
        safe_name = "".join(c for c in base_name if c.isalnum() or c in ("-", "_"))[:50]
        return f"{safe_name}_{unique_id}{ext}"

    async def save_upload_file(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        Save uploaded file to B-roll directory.

        Returns:
            Tuple of (filename, file_path, file_size)
        """
        logger.info(f"Saving uploaded file: {file.filename}")
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Validate file type
        if not (
            self._is_video_file(file.filename) or self._is_image_file(file.filename)
        ):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only video and image files are allowed.",
            )

        # Generate unique filename
        filename = self._generate_unique_filename(file.filename)
        file_path = self.broll_dir / filename

        # Save file
        try:
            content = await file.read()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            file_size = len(content)
            logger.info(f"File saved: {file_path} (size: {file_size} bytes)")
            return filename, str(file_path.relative_to(self.broll_dir)), file_size

        except Exception as e:
            # Clean up file if something went wrong
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Error saving file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    def delete_file(self, filename: str) -> bool:
        """Delete B-roll file from filesystem."""
        logger.info(f"Deleting B-roll file: {filename}")
        try:
            file_path = self.broll_dir / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return False

    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get basic file information."""
        file_path = self.broll_dir / filename

        if not file_path.exists():
            return None

        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))

        return {
            "filename": filename,
            "file_size": stat.st_size,
            "mime_type": mime_type or "application/octet-stream",
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
        }

    async def extract_video_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Extract video metadata using existing B-roll meta extractor.
        This integrates with the existing b_roll/meta_extractor.py
        """
        logger.info(f"Extracting metadata for video file: {filename}")
        try:
            # Import the existing meta extractor
            # Add parent directory to Python path to find b_roll module
            import sys
            from pathlib import Path

            parent_dir = Path(__file__).parent.parent.parent
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))

            from b_roll.meta_extractor import MetaExtractor
            import os

            file_path = self.broll_dir / filename
            if not file_path.exists():
                return None

            # Load OpenAI API key from environment or config
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                # Try to load from config.yml
                logger.info("Loading OpenAI API key from config.yml")
                try:
                    import yaml

                    # Use a more robust way to find config.yml
                    current_dir = Path.cwd()
                    config_path = None

                    # Try different possible locations for config.yml
                    possible_paths = [
                        current_dir / "config.yml",
                        current_dir.parent / "config.yml",
                        Path("/home/kostiantyn/projects/storyforge/config.yml"),
                        self.broll_dir.parent / "config.yml",
                    ]

                    for path in possible_paths:
                        if path.exists():
                            config_path = path
                            break

                    if config_path and config_path.exists():
                        with open(config_path, "r") as f:
                            config = yaml.safe_load(f)
                        openai_api_key = (
                            config.get("api", {}).get("openai", {}).get("api_key")
                        )
                        logger.info(f"Loaded OpenAI API key from {config_path}")
                except Exception as e:
                    logger.warning(f"Could not load config.yml: {e}")
                    pass

            config = {
                "paths": {"b_roll": str(self.broll_dir)},
                "api": {"openai": {"api_key": openai_api_key, "model": "gpt-4o"}},
            }

            extractor = MetaExtractor(config)

            logger.info(f"Processing video for metadata extraction: {file_path}")

            # Use the existing process_video method
            success = extractor.process_video(str(file_path))

            if success:
                # Try to read the generated .txt file with analysis
                txt_name = file_path.stem + ".txt"
                txt_path = file_path.parent / txt_name

                if txt_path.exists():
                    with open(txt_path, "r", encoding="utf-8") as f:
                        context = f.read().strip()

                    logger.info(f"Metadata extracted for {file_path}: {context}")

                    return {
                        "analysis": context,
                        "has_metadata": True,
                        "extracted_at": file_path.stat().st_mtime,
                    }
                else:
                    logger.warning(
                        f"Metadata file not found for {file_path}: {txt_path}"
                    )
            return {
                "analysis": None,
                "has_metadata": False,
                "error": "Failed to extract metadata",
            }

        except ImportError:
            # If meta extractor is not available, return basic info
            return None
        except Exception as e:
            logger.error(f"Error extracting metadata for {filename}: {e}")
            return None

    def get_file_url(self, filename: str) -> str:
        """Get URL for accessing the B-roll file."""
        return f"/api/broll/files/{filename}"

    def search_files(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Search B-roll files by various criteria.
        This is a basic implementation - can be enhanced with database search.
        """
        files = []

        for file_path in self.broll_dir.glob("*"):
            if file_path.is_file() and (
                self._is_video_file(file_path.name)
                or self._is_image_file(file_path.name)
            ):
                # Basic filename matching
                if query and query.lower() not in file_path.name.lower():
                    continue

                files.append(file_path.name)

        return files

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for B-roll directory."""
        total_size = 0
        file_count = 0
        video_count = 0
        image_count = 0

        for file_path in self.broll_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1

                if self._is_video_file(file_path.name):
                    video_count += 1
                elif self._is_image_file(file_path.name):
                    image_count += 1

        return {
            "total_files": file_count,
            "video_files": video_count,
            "image_files": image_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "directory_path": str(self.broll_dir),
        }
