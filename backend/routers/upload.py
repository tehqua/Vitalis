"""
File upload router — stores files in MongoDB GridFS (no local disk).
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
from datetime import datetime

from ..schemas import FileUploadResponse
from ..validators import FileValidator
from ..config import get_settings, Settings
from ..auth import get_current_user, TokenData
from ..database import get_db, Database

logger = logging.getLogger(__name__)

router = APIRouter()


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

async def _read_and_validate(
    file: UploadFile,
    kind: str,          # "image" | "audio"
    settings: Settings,
):
    """Validate extension + content-type, read bytes, return (bytes, size)."""
    is_valid, error = FileValidator.validate_file_extension(file.filename, kind)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    expected_prefix = f"{kind}/"
    if file.content_type and not file.content_type.startswith(expected_prefix):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {file.content_type}. Expected {expected_prefix}*",
        )

    content = await file.read()
    size_bytes = len(content)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size_bytes / 1024 / 1024:.1f} MB). Max {settings.MAX_FILE_SIZE_MB} MB.",
        )
    return content, size_bytes


# --------------------------------------------------------------------------- #
# Upload endpoints                                                              #
# --------------------------------------------------------------------------- #

@router.post("/image", response_model=FileUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="Image file — stored in MongoDB GridFS"),
    current_user: TokenData = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: Database = Depends(get_db),
):
    """
    Upload an image file.

    Binary content is persisted in **MongoDB GridFS** (not on local disk).
    Use `GET /upload/file/{file_id}` to retrieve the raw bytes later.

    Supported formats: JPG, JPEG, PNG, GIF, WEBP — Max 10 MB (configurable)
    """
    logger.info(
        f"Image upload: patient={current_user.patient_id} "
        f"file={file.filename} type={file.content_type}"
    )
    try:
        content, size_bytes = await _read_and_validate(file, "image", settings)

        file_id = await db.save_upload(
            patient_id=current_user.patient_id,
            session_id=current_user.session_id,
            filename=file.filename,
            file_content=content,
            file_type="image",
            size_bytes=size_bytes,
            content_type=file.content_type or "image/jpeg",
        )

        file_url = f"/api/upload/file/{file_id}"
        logger.info(f"Image stored in GridFS: file_id={file_id} ({size_bytes / 1024:.1f} KB)")

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=file_url,   # reuse field to hold the serve URL
            file_type="image",
            size_bytes=size_bytes,
            uploaded_at=datetime.utcnow().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")


@router.post("/audio", response_model=FileUploadResponse)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file — stored in MongoDB GridFS"),
    current_user: TokenData = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    db: Database = Depends(get_db),
):
    """
    Upload an audio file.

    Binary content is persisted in **MongoDB GridFS** (not on local disk).
    Use `GET /upload/file/{file_id}` to retrieve the raw bytes later.

    Supported formats: WAV, MP3, M4A, OGG — Max 10 MB (configurable)
    """
    logger.info(
        f"Audio upload: patient={current_user.patient_id} "
        f"file={file.filename} type={file.content_type}"
    )
    try:
        content, size_bytes = await _read_and_validate(file, "audio", settings)

        file_id = await db.save_upload(
            patient_id=current_user.patient_id,
            session_id=current_user.session_id,
            filename=file.filename,
            file_content=content,
            file_type="audio",
            size_bytes=size_bytes,
            content_type=file.content_type or "audio/wav",
        )

        file_url = f"/api/upload/file/{file_id}"
        logger.info(f"Audio stored in GridFS: file_id={file_id} ({size_bytes / 1024:.1f} KB)")

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=file_url,
            file_type="audio",
            size_bytes=size_bytes,
            uploaded_at=datetime.utcnow().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload audio: {e}")


# --------------------------------------------------------------------------- #
# Serve / info / delete                                                         #
# --------------------------------------------------------------------------- #

@router.get("/file/{file_id}")
async def serve_upload_file(
    file_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Stream the raw binary content of an uploaded file from GridFS.

    Returns the file with its original MIME type so browsers/clients can
    render images or play audio directly.
    """
    stream, doc = await db.get_upload_file_stream(file_id=file_id)
    if not stream or not doc:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    if doc.get("patient_id") != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    content_type = doc.get("content_type", "application/octet-stream")
    filename = doc.get("filename", "download")

    async def _generator():
        while chunk := await stream.readchunk():
            yield chunk

    return StreamingResponse(
        _generator(),
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/info/{file_id}")
async def get_upload_info(
    file_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Get metadata for an uploaded file (no binary content)."""
    doc = await db.get_upload(file_id=file_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    if doc.get("patient_id") != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "file_id": doc["file_id"],
        "filename": doc["filename"],
        "file_type": doc["file_type"],
        "content_type": doc.get("content_type"),
        "size_bytes": doc["size_bytes"],
        "uploaded_at": (
            doc["uploaded_at"].isoformat()
            if isinstance(doc["uploaded_at"], datetime)
            else doc["uploaded_at"]
        ),
        "file_url": f"/api/upload/file/{file_id}",
        "session_id": doc.get("session_id"),
    }


@router.delete("/{file_id}")
async def delete_upload(
    file_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """Delete a file from GridFS and its metadata record."""
    # Verify existence + ownership first
    doc = await db.get_upload(file_id=file_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    if doc.get("patient_id") != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    deleted = await db.delete_upload(file_id=file_id, patient_id=current_user.patient_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Delete failed unexpectedly")

    return {"message": "File deleted successfully", "file_id": file_id}


@router.get("/my-uploads")
async def list_my_uploads(
    file_type: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """List all uploads for the current user."""
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
                "file_url": f"/api/upload/file/{d['file_id']}",
                "uploaded_at": (
                    d["uploaded_at"].isoformat()
                    if isinstance(d["uploaded_at"], datetime)
                    else d["uploaded_at"]
                ),
            }
            for d in docs
        ],
    }


@router.get("/limits")
async def get_upload_limits(settings: Settings = Depends(get_settings)):
    """Get upload size limits and allowed file formats."""
    return {
        "image": {
            "max_size_mb": settings.MAX_FILE_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_IMAGE_EXTENSIONS,
            "mime_types": ["image/jpeg", "image/png", "image/gif", "image/webp"],
            "storage": "MongoDB GridFS",
        },
        "audio": {
            "max_size_mb": settings.MAX_FILE_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_AUDIO_EXTENSIONS,
            "mime_types": ["audio/wav", "audio/mpeg", "audio/mp4", "audio/ogg"],
            "storage": "MongoDB GridFS",
            "recommendations": {"format": "WAV", "sample_rate": "16kHz", "channels": "mono"},
        },
    }