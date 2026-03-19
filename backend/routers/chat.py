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
    ConversationMessage
)
from ..auth import get_current_user, TokenData
from ..services.orchestrator_service import get_orchestrator_service, OrchestratorService
from ..services.file_service import save_uploaded_file

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
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Clear conversation history for current session.
    
    Note: This only clears the in-memory conversation context,
    not the database records.
    
    Args:
        current_user: Authenticated user data
        orchestrator: Orchestrator service
        
    Returns:
        Confirmation message
    """
    await orchestrator.clear_memory(current_user.session_id)
    
    return {"message": "Conversation history cleared"}


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