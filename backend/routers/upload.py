"""
File upload router with validation, database records, and error handling.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import Optional
import logging
import os
from datetime import datetime

from ..schemas import FileUploadResponse
from ..services.file_service import save_uploaded_file, get_file_info, validate_file_path
from ..config import get_settings, Settings
from ..auth import get_current_user, TokenData
from ..validators import FileValidator
from ..database import get_db, Database

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/image", response_model=FileUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: TokenData = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: Database = Depends(get_db)
):
    """
    Upload an image file.

    Accepts image files for skin condition analysis. The uploaded file
    will be validated for type, size, and content before saving.
    A database record is created so the file can be retrieved or deleted later.

    Supported formats: JPG, JPEG, PNG, GIF, WEBP
    Maximum size: 10MB (configurable)

    Args:
        file: Image file to upload
        current_user: Authenticated user
        settings: Application settings
        db: Database instance

    Returns:
        File upload response with file details and stable file_id

    Raises:
        HTTPException: If validation fails or upload error occurs
    """
    logger.info(
        f"Image upload request from patient {current_user.patient_id}: "
        f"{file.filename} ({file.content_type})"
    )

    try:
        # Validate filename
        is_valid, error = FileValidator.validate_file_extension(
            file.filename,
            "image"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Validate content type
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content type: {file.content_type}. Expected image/*"
            )

        # Save file to disk
        file_path = await save_uploaded_file(
            file=file,
            upload_dir=settings.UPLOAD_DIR,
            file_type="image",
            allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS,
            max_size_mb=settings.MAX_FILE_SIZE_MB
        )

        # Get file info
        file_info = await get_file_info(file_path)
        size_bytes = file_info.get("size_bytes", 0)

        # Save to database — generates a stable UUID file_id
        file_id = await db.save_upload(
            patient_id=current_user.patient_id,
            session_id=current_user.session_id,
            filename=file.filename,
            file_path=file_path,
            file_type="image",
            size_bytes=size_bytes,
        )

        logger.info(
            f"Image uploaded successfully: {file_path} "
            f"({file_info.get('size_mb', 0):.2f}MB) | file_id={file_id}"
        )

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_type="image",
            size_bytes=size_bytes,
            uploaded_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.post("/audio", response_model=FileUploadResponse)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file to upload"),
    current_user: TokenData = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: Database = Depends(get_db)
):
    """
    Upload an audio file.

    Accepts audio files for speech-to-text transcription. The uploaded
    file will be validated for type, size, and content before saving.
    A database record is created so the file can be retrieved or deleted later.

    Supported formats: WAV, MP3, M4A, OGG
    Maximum size: 50MB (configurable)
    Recommended: WAV, 16kHz, mono

    Args:
        file: Audio file to upload
        current_user: Authenticated user
        settings: Application settings
        db: Database instance

    Returns:
        File upload response with file details and stable file_id

    Raises:
        HTTPException: If validation fails or upload error occurs
    """
    logger.info(
        f"Audio upload request from patient {current_user.patient_id}: "
        f"{file.filename} ({file.content_type})"
    )

    try:
        # Validate filename
        is_valid, error = FileValidator.validate_file_extension(
            file.filename,
            "audio"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Validate content type
        if file.content_type and not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content type: {file.content_type}. Expected audio/*"
            )

        # Save file to disk
        file_path = await save_uploaded_file(
            file=file,
            upload_dir=settings.UPLOAD_DIR,
            file_type="audio",
            allowed_extensions=settings.ALLOWED_AUDIO_EXTENSIONS,
            max_size_mb=settings.MAX_FILE_SIZE_MB
        )

        # Get file info
        file_info = await get_file_info(file_path)
        size_bytes = file_info.get("size_bytes", 0)

        # Save to database — generates a stable UUID file_id
        file_id = await db.save_upload(
            patient_id=current_user.patient_id,
            session_id=current_user.session_id,
            filename=file.filename,
            file_path=file_path,
            file_type="audio",
            size_bytes=size_bytes,
        )

        logger.info(
            f"Audio uploaded successfully: {file_path} "
            f"({file_info.get('size_mb', 0):.2f}MB) | file_id={file_id}"
        )

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_type="audio",
            size_bytes=size_bytes,
            uploaded_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}"
        )


@router.get("/info/{file_id}")
async def get_upload_info(
    file_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Get information about an uploaded file.

    Retrieves metadata for a previously uploaded file including original
    filename, type, size, and upload timestamp. Users can only view
    files they uploaded themselves.

    Args:
        file_id: File UUID from upload response
        current_user: Authenticated user
        db: Database instance

    Returns:
        File metadata dictionary

    Raises:
        HTTPException 404: If file not found or not owned by current user
    """
    doc = await db.get_upload(file_id=file_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )

    # Ownership check — patients can only see their own files
    if doc.get("patient_id") != current_user.patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this file"
        )

    return {
        "file_id": doc["file_id"],
        "filename": doc["filename"],
        "file_type": doc["file_type"],
        "size_bytes": doc["size_bytes"],
        "uploaded_at": doc["uploaded_at"].isoformat() if isinstance(doc["uploaded_at"], datetime) else doc["uploaded_at"],
        "session_id": doc.get("session_id"),
    }


@router.delete("/{file_id}")
async def delete_upload(
    file_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Delete an uploaded file.

    Removes a previously uploaded file from both disk storage and the
    database. Users can only delete files they uploaded themselves.

    Args:
        file_id: File UUID from upload response
        current_user: Authenticated user
        db: Database instance

    Returns:
        Deletion confirmation

    Raises:
        HTTPException 404: If file not found or not owned by current user
    """
    # Fetch record first to get the disk path and verify ownership
    doc = await db.get_upload(file_id=file_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )

    if doc.get("patient_id") != current_user.patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this file"
        )

    # Delete from disk
    file_path = doc.get("file_path")
    disk_deleted = False
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            disk_deleted = True
            logger.info(f"Deleted file from disk: {file_path}")
        except OSError as e:
            logger.warning(f"Could not delete file from disk ({file_path}): {e}")

    # Delete DB record (ownership already verified above)
    await db.delete_upload(file_id=file_id, patient_id=current_user.patient_id)

    return {
        "message": "File deleted successfully",
        "file_id": file_id,
        "disk_deleted": disk_deleted,
    }


@router.get("/my-uploads")
async def list_my_uploads(
    file_type: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    List all uploads for the current user.

    Args:
        file_type: Optional filter ('image' or 'audio')
        current_user: Authenticated user
        db: Database instance

    Returns:
        List of upload records (newest first)
    """
    docs = await db.get_patient_uploads(
        patient_id=current_user.patient_id,
        file_type=file_type,
    )

    return {
        "patient_id": current_user.patient_id,
        "total": len(docs),
        "uploads": [
            {
                "file_id": d["file_id"],
                "filename": d["filename"],
                "file_type": d["file_type"],
                "size_bytes": d["size_bytes"],
                "uploaded_at": d["uploaded_at"].isoformat() if isinstance(d["uploaded_at"], datetime) else d["uploaded_at"],
            }
            for d in docs
        ],
    }


@router.get("/limits")
async def get_upload_limits(
    settings: Settings = Depends(get_settings)
):
    """
    Get upload size limits and allowed formats.

    Returns configuration for file uploads including maximum sizes
    and allowed extensions for each file type.

    Args:
        settings: Application settings

    Returns:
        Upload limits and allowed formats
    """
    return {
        "image": {
            "max_size_mb": settings.MAX_FILE_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_IMAGE_EXTENSIONS,
            "mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp"]
        },
        "audio": {
            "max_size_mb": settings.MAX_FILE_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_AUDIO_EXTENSIONS,
            "mime_types": ["audio/wav", "audio/mpeg", "audio/mp4", "audio/ogg"],
            "recommendations": {
                "format": "WAV",
                "sample_rate": "16kHz",
                "channels": "mono"
            }
        }
    }