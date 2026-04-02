"""
Chat router - main conversation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import Optional
import uuid
import logging
from datetime import datetime

from ..config import get_settings, Settings
from ..database import get_db, Database
from ..schemas import (
    ChatRequest,
    ChatResponse,
    ChatWithImageRequest,
    ChatWithAudioRequest,
    ConversationHistoryResponse,
    ConversationMessage,
    PatientRecordResponse
)
from ..auth import get_current_user, TokenData
from ..services.orchestrator_service import get_orchestrator_service, OrchestratorService
from ..services.file_service import save_uploaded_file
from ..services.patient_record_service import generate_patient_record

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    db: Database = Depends(get_db)
):
    """
    Send a text message to the chatbot.
    
    This endpoint processes a text-only message through the orchestrator
    and returns the agent's response.
    
    Args:
        request: Chat request with message
        current_user: Authenticated user data
        orchestrator: Orchestrator service
        db: Database instance
        
    Returns:
        Chat response from agent
    """
    logger.info(
        f"Chat message from patient {current_user.patient_id}: "
        f"{request.message[:50]}..."
    )
    
    try:
        # Process message through orchestrator
        result = await orchestrator.process_message(
            patient_id=current_user.patient_id,
            text_input=request.message,
            session_id=current_user.session_id,
            db=db
        )
        
        # Save to database
        await db.save_conversation(
            session_id=current_user.session_id,
            patient_id=current_user.patient_id,
            message=request.message,
            response=result["response"],
            metadata=result.get("metadata", {})
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=current_user.session_id,
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/message-with-image", response_model=ChatResponse)
async def send_message_with_image(
    message: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Send a message with an image attachment.
    
    The image will be analyzed for skin conditions and the analysis
    will be included in the agent's response.
    
    Args:
        message: Optional text message
        image: Uploaded image file
        current_user: Authenticated user data
        orchestrator: Orchestrator service
        db: Database instance
        settings: Application settings
        
    Returns:
        Chat response including image analysis
    """
    logger.info(
        f"Chat with image from patient {current_user.patient_id}: "
        f"{image.filename}"
    )
    
    try:
        # Save uploaded image
        image_path = await save_uploaded_file(
            file=image,
            upload_dir=settings.UPLOAD_DIR,
            file_type="image",
            allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS,
            max_size_mb=settings.MAX_FILE_SIZE_MB
        )
        
        # Process through orchestrator
        result = await orchestrator.process_message(
            patient_id=current_user.patient_id,
            text_input=message,
            image_file_path=image_path,
            session_id=current_user.session_id,
            db=db
        )
        
        # Save to database
        await db.save_conversation(
            session_id=current_user.session_id,
            patient_id=current_user.patient_id,
            message=message or f"[Image: {image.filename}]",
            response=result["response"],
            metadata={
                **result.get("metadata", {}),
                "image_path": image_path,
                "image_filename": image.filename
            }
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=current_user.session_id,
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing message with image: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message with image: {str(e)}"
        )


@router.post("/message-with-audio", response_model=ChatResponse)
async def send_message_with_audio(
    audio: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Send an audio message.
    
    The audio will be transcribed to text using speech-to-text
    and then processed by the agent.
    
    Args:
        audio: Uploaded audio file
        current_user: Authenticated user data
        orchestrator: Orchestrator service
        db: Database instance
        settings: Application settings
        
    Returns:
        Chat response including transcription
    """
    logger.info(
        f"Chat with audio from patient {current_user.patient_id}: "
        f"{audio.filename}"
    )
    
    try:
        # Save uploaded audio
        audio_path = await save_uploaded_file(
            file=audio,
            upload_dir=settings.UPLOAD_DIR,
            file_type="audio",
            allowed_extensions=settings.ALLOWED_AUDIO_EXTENSIONS,
            max_size_mb=settings.MAX_FILE_SIZE_MB
        )
        
        # Process through orchestrator
        result = await orchestrator.process_message(
            patient_id=current_user.patient_id,
            audio_file_path=audio_path,
            session_id=current_user.session_id,
            db=db
        )
        
        # Save to database
        await db.save_conversation(
            session_id=current_user.session_id,
            patient_id=current_user.patient_id,
            message=f"[Audio: {audio.filename}]",
            response=result["response"],
            metadata={
                **result.get("metadata", {}),
                "audio_path": audio_path,
                "audio_filename": audio.filename
            }
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=current_user.session_id,
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error processing audio message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio message: {str(e)}"
        )


@router.get("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    limit: int = 50,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Get conversation history for current session.
    
    Args:
        limit: Maximum number of messages to return
        current_user: Authenticated user data
        db: Database instance
        
    Returns:
        Conversation history
    """
    conversations = await db.get_conversation_history(
        session_id=current_user.session_id,
        limit=limit
    )
    
    messages = []
    for conv in conversations:
        # Add user message
        messages.append(ConversationMessage(
            role="user",
            content=conv["message"],
            timestamp=conv["created_at"],
            metadata=None
        ))
        # Add assistant response
        messages.append(ConversationMessage(
            role="assistant",
            content=conv["response"],
            timestamp=conv["created_at"],
            metadata=conv.get("metadata")
        ))
    
    return ConversationHistoryResponse(
        session_id=current_user.session_id,
        patient_id=current_user.patient_id,
        messages=messages,
        total_messages=len(messages)
    )


@router.delete("/history")
async def clear_conversation_history(
    current_user: TokenData = Depends(get_current_user),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    db: Database = Depends(get_db)
):
    """
    Clear conversation history for current session (memory + database).

    Deletes all conversation documents for the current session from MongoDB
    and clears the in-memory LangGraph context.

    Args:
        current_user: Authenticated user data
        orchestrator: Orchestrator service
        db: Database instance

    Returns:
        Confirmation message with count of deleted records
    """
    await orchestrator.clear_memory(current_user.session_id)
    deleted = await db.delete_session_conversations(
        session_id=current_user.session_id,
        patient_id=current_user.patient_id,
    )
    return {"message": "Conversation history cleared", "deleted_count": deleted}


@router.delete("/history/{session_id}")
async def delete_session_history(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    db: Database = Depends(get_db)
):
    """
    Delete all conversation records for a specific past session.

    Ownership is enforced: the patient can only delete their own sessions.
    Returns 404 if the session doesn't exist or belongs to another patient.

    Args:
        session_id: Target session identifier
        current_user: Authenticated user data
        orchestrator: Orchestrator service
        db: Database instance

    Returns:
        Confirmation message with session_id and deleted_count
    """
    deleted = await db.delete_session_conversations(
        session_id=session_id,
        patient_id=current_user.patient_id,
    )
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )
    # Clear in-memory context in case the session was still loaded
    await orchestrator.clear_memory(session_id)
    logger.info(
        f"Session {session_id} deleted by patient {current_user.patient_id} "
        f"({deleted} message(s) removed)"
    )
    return {"message": "Session deleted", "session_id": session_id, "deleted_count": deleted}


@router.get("/sessions")
async def get_patient_sessions(
    limit: int = 20,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Get a list of all chat sessions for the current patient.

    Returns sessions sorted newest-first. Each item has:
    - session_id, first_message (title), started_at, last_activity, message_count

    Used by the Sidebar to render the per-session Recent History list.
    """
    sessions = await db.get_patient_sessions(
        patient_id=current_user.patient_id,
        limit=limit
    )

    result = []
    for s in sessions:
        result.append({
            "session_id":    s["session_id"],
            "first_message": s.get("first_message", ""),
            "started_at":    s["started_at"].isoformat() if s.get("started_at") else None,
            "last_activity": s["last_activity"].isoformat() if s.get("last_activity") else None,
            "message_count": s.get("message_count", 0),
        })

    return {"patient_id": current_user.patient_id, "sessions": result, "total": len(result)}


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_session_history(
    session_id: str,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    Get full conversation history for a specific session.

    Ownership is verified — patients can only retrieve their own sessions.
    Used when the user clicks a session item in the Sidebar.
    """
    conversations = await db.get_conversation_history(
        session_id=session_id,
        limit=limit
    )

    for conv in conversations:
        if conv.get("patient_id") != current_user.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )

    messages = []
    for conv in conversations:
        messages.append(ConversationMessage(
            role="user",
            content=conv["message"],
            timestamp=conv["created_at"],
            metadata=None
        ))
        messages.append(ConversationMessage(
            role="assistant",
            content=conv["response"],
            timestamp=conv["created_at"],
            metadata=conv.get("metadata")
        ))

    return ConversationHistoryResponse(
        session_id=session_id,
        patient_id=current_user.patient_id,
        messages=messages,
        total_messages=len(messages)
    )


@router.get("/patient-record", response_model=PatientRecordResponse)
async def get_patient_record(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Parse the patient's FHIR bundle and return a full structured medical record report.

    The report is built directly from the FHIR JSON file — no LLM or RAG retrieval involved.
    Results are returned immediately; the heavy lifting is pure Python parsing.

    Triggered when the user clicks "Personal Records" in the Sidebar.
    """
    from datetime import datetime as _dt

    logger.info(f"Patient record requested for: {current_user.patient_id}")

    try:
        result = generate_patient_record(current_user.patient_id)
        return PatientRecordResponse(
            patient_id=current_user.patient_id,
            patient_name=result["patient_name"],
            report_text=result["report_text"],
            sections=result["sections"],
            generated_at=_dt.utcnow().isoformat() + "Z",
        )

    except FileNotFoundError as exc:
        logger.warning(f"FHIR record not found: {exc}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No medical record found for this patient.",
        )

    except ValueError as exc:
        logger.error(f"FHIR parse error for {current_user.patient_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse medical record: {exc}",
        )

    except Exception as exc:
        logger.error(f"Unexpected error generating patient record: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while loading the patient record.",
        )