"""
Pydantic schemas for API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


# Authentication schemas

class LoginRequest(BaseModel):
    """Login request schema"""
    patient_id: str = Field(..., description="Patient identifier")
    
    @validator('patient_id')
    def validate_patient_id(cls, v):
        """Validate patient ID format"""
        if not v or len(v) < 10:
            raise ValueError("Invalid patient ID format")
        return v


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    token_type: str = "bearer"
    session_id: str
    patient_id: str
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    patient_id: str
    session_id: str


# Chat schemas

class ChatRequest(BaseModel):
    """Chat message request schema"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I have a headache for 2 days",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    timestamp: str = Field(..., description="Response timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on your symptoms, you may have a tension headache...",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {
                    "input_type": "text",
                    "tools_used": [],
                    "emergency_detected": False
                }
            }
        }


class ChatWithImageRequest(BaseModel):
    """Chat with image request schema"""
    message: Optional[str] = Field(None, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID")


class ChatWithAudioRequest(BaseModel):
    """Chat with audio request schema"""
    session_id: Optional[str] = Field(None, description="Session ID")


# Conversation history schemas

class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    session_id: str
    patient_id: str
    messages: List[ConversationMessage]
    total_messages: int


# File upload schemas

class FileUploadResponse(BaseModel):
    """File upload response"""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Server file path")
    file_type: str = Field(..., description="File type: image or audio")
    size_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: str = Field(..., description="Upload timestamp")


# Health check schemas

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    orchestrator_status: str = Field(..., description="Orchestrator status")
    database_status: str = Field(..., description="Database status")
    ollama_status: str = Field(..., description="Ollama status")


# Error schemas

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type")
    timestamp: Optional[str] = Field(None, description="Error timestamp")


# Statistics schemas

class SessionStatistics(BaseModel):
    """Session statistics"""
    session_id: str
    patient_id: str
    total_messages: int
    started_at: datetime
    last_activity: datetime
    active: bool


class PatientStatistics(BaseModel):
    """Patient statistics"""
    patient_id: str
    total_sessions: int
    total_messages: int
    total_images_analyzed: int
    total_audio_transcribed: int
    emergency_detections: int
    first_interaction: Optional[datetime]
    last_interaction: Optional[datetime]


# Patient record report schemas

class PatientRecordResponse(BaseModel):
    """
    Response returned by GET /api/chat/patient-record.
    Contains a full structured medical record report parsed from the
    patient's FHIR bundle — no LLM involved.
    """
    patient_id: str = Field(..., description="Patient identifier")
    patient_name: str = Field(..., description="Full name extracted from FHIR bundle")
    report_text: str = Field(..., description="Full formatted report as plain text")
    sections: Dict[str, str] = Field(
        default_factory=dict,
        description="Individual report sections keyed by section ID"
    )
    generated_at: str = Field(..., description="Report generation timestamp")