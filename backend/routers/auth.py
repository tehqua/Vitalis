"""
Authentication router.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from datetime import timedelta, datetime
from typing import Optional
import uuid
import logging

from ..config import get_settings, Settings
from ..database import get_db, Database
from ..schemas import LoginRequest, LoginResponse
from ..auth import create_access_token, validate_patient_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    settings: Settings = Depends(get_settings),
    db: Database = Depends(get_db)
):
    """
    Authenticate patient and create session.

    The patient_id IS the activation code provided by admin.
    Format: FirstName###_LastName###_uuid
    """
    patient_id = request.patient_id

    # Validate patient ID format
    if not validate_patient_id(patient_id):
        logger.warning(f"Invalid patient ID format: {patient_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid patient ID format"
        )

    # Verify patient code exists and is not revoked
    code_doc = await db.db.patient_codes.find_one({"patient_id": patient_id})
    if code_doc:
        if code_doc.get("status") == "Revoked":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This Patient ID has been revoked. Please contact your clinic."
            )
        # Mark as Used on first login
        if not code_doc.get("first_login_at"):
            await db.db.patient_codes.update_one(
                {"patient_id": patient_id},
                {"$set": {"status": "Used", "first_login_at": datetime.utcnow()}}
            )
    # If patient_codes collection doesn't exist yet (legacy), allow valid format

    # Create session
    session_id = str(uuid.uuid4())
    await db.create_session(
        session_id=session_id,
        patient_id=patient_id,
        expires_in_minutes=settings.SESSION_EXPIRE_MINUTES
    )
    logger.info(f"Session created for patient: {patient_id}")

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"patient_id": patient_id, "session_id": session_id},
        settings=settings,
        expires_delta=access_token_expires
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        session_id=session_id,
        patient_id=patient_id,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    session_id: str,
    db: Database = Depends(get_db)
):
    """Logout and invalidate session."""
    await db.invalidate_session(session_id)
    logger.info(f"Session invalidated: {session_id}")
    return {"message": "Logged out successfully"}


# ─── Forgot ID (patient-facing) ───────────────────────────────────────────────

class ForgotIdRequest(BaseModel):
    """Submitted by patient on LoginPage when they forget their Patient ID."""
    name: str = Field(..., min_length=2, max_length=100)
    dob: str = Field(..., description="Date of birth YYYY-MM-DD")
    phone: str = Field(..., min_length=6, max_length=20)
    email: str = Field(..., min_length=5, max_length=200)
    visit_date: str = Field(..., description="Approximate visit date")
    department: str = Field(default="Unknown", max_length=100)
    notes: Optional[str] = Field(default="", max_length=500)


@router.post("/forgot-id", status_code=202)
async def forgot_id(
    req: ForgotIdRequest,
    db: Database = Depends(get_db),
):
    """
    Patient submits a Forgot-ID request.

    Creates a support_ticket with type=forgot_id and status=New.
    Admin sees this in the 'Forgot ID Requests' panel with all patient info
    so they can look it up and contact the patient directly.

    Returns 202 Accepted immediately.
    """
    # Generate sequential ticket ID
    count = await db.db.support_tickets.count_documents({"type": "forgot_id"})
    ticket_id = f"FRQ-{count + 1:03d}"

    ticket = {
        "ticket_id": ticket_id,
        "type": "forgot_id",
        "name": req.name.strip(),
        "dob": req.dob,
        "phone": req.phone.strip(),
        "email": req.email.strip().lower(),
        "visit_date": req.visit_date,
        "department": req.department,
        "notes": req.notes or "",
        "status": "New",
        "submitted_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await db.db.support_tickets.insert_one(ticket)
    logger.info(f"Forgot-ID ticket created: {ticket_id} for {req.name}")

    return {
        "message": "Your request has been received. A clinic staff member will contact you shortly.",
        "ticket_id": ticket_id,
    }