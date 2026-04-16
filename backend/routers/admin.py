"""
Admin API router.

Provides endpoints for the Vitalis Admin Panel (vitalis-care-hub).
All endpoints require admin JWT authentication via ADMIN_SECRET_KEY.

Collections used (all Read-Only except where noted):
  - sessions          : patient session records (read)
  - conversations     : chat history (read)
  - medications       : medication schedules (read/write by admin)
  - reminder_logs     : email reminder history (read)
  - support_tickets   : Forgot-ID requests created by patients (read/write)

Data integrity rule: FHIR records in patient database are NEVER modified.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
import logging
import uuid

from ..config import get_settings, Settings
from ..database import get_db, Database

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Admin Auth ──────────────────────────────────────────────────────────────

def verify_admin(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Simple admin authentication via shared ADMIN_SECRET_KEY.
    In production, replace with full admin JWT issuance flow.

    The Admin Panel stores its token in sessionStorage under 'admin_token'.
    The token is the raw ADMIN_SECRET_KEY for the MVP; upgrade to signed JWT later.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin credentials required",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials",
        )
    return token


# ─── Schemas ─────────────────────────────────────────────────────────────────

class OverviewStats(BaseModel):
    active_patients: int
    sessions_today: int
    reminders_sent_today: int
    pending_codes: int
    new_forgot_requests: int


class ActivityItem(BaseModel):
    time: str
    type: str
    patient: str
    status: str


class SystemService(BaseModel):
    name: str
    status: str  # Operational | Degraded | Down


class PatientOut(BaseModel):
    id: str
    name: str
    status: str
    consented: bool
    consent_date: str
    last_session: str
    sessions: int
    email: Optional[str] = None
    phone: Optional[str] = None


class CreatePatientRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: Optional[str] = None
    phone: Optional[str] = None


class PatientCodeOut(BaseModel):
    patient_id: str        # IS the login code: FirstName###_LastName###_uuid
    patient_name: str
    issued_at: str
    status: str            # Active | Used | Revoked
    first_login_at: Optional[str] = None


class MedicationOut(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    medication: str
    dosage: str
    frequency: str
    times: List[str]
    start_date: str
    end_date: Optional[str] = None
    reminders_sent: int
    reminders_total: int
    status: str            # Active | Paused | Completed


class CreateMedicationRequest(BaseModel):
    patient_id: str
    patient_name: str
    medication: str
    dosage: str
    frequency: str
    times: List[str]
    start_date: str
    end_date: Optional[str] = None
    patient_email: Optional[str] = None
    notes: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str


class ReminderLogOut(BaseModel):
    id: str
    sent_at: str
    patient_name: str
    medication: str
    email_masked: str
    status: str            # Delivered | Failed | Pending
    error: Optional[str] = None


class ForgotRequestOut(BaseModel):
    id: str
    submitted_at: str
    name: str
    dob: str
    phone: str
    email: str
    visit_date: str
    department: str
    notes: str
    status: str            # New | In Progress | Resolved


# ─── Helper ──────────────────────────────────────────────────────────────────

def _fmt_time(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.strftime("%b %d, %Y %I:%M %p")


def _relative_time(dt: Optional[datetime]) -> str:
    """Return human-readable relative time string."""
    if not dt:
        return "Never"
    delta = datetime.utcnow() - dt
    if delta.total_seconds() < 3600:
        mins = int(delta.total_seconds() / 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    if delta.total_seconds() < 86400:
        hrs = int(delta.total_seconds() / 3600)
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    days = delta.days
    return f"{days} day{'s' if days != 1 else ''} ago"


# ─── Overview ────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=OverviewStats)
async def get_stats(
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """Dashboard statistics — derive counts from MongoDB in real-time."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Active patients = distinct patient_ids with an active session
    active_patient_ids = await db.db.sessions.distinct(
        "patient_id",
        {"active": True, "expires_at": {"$gt": now}}
    )

    # Sessions started today
    sessions_today = await db.db.sessions.count_documents({
        "created_at": {"$gte": today_start}
    })

    # Reminders sent today
    reminders_today = await db.db.reminder_logs.count_documents({
        "sent_at": {"$gte": today_start},
        "status": "Delivered"
    })

    # Patient IDs that have never logged in (= code is still Active / unused)
    pending_codes = await db.db.patient_codes.count_documents({"status": "Active"})

    # New (unresolved) Forgot-ID requests
    new_forgot = await db.db.support_tickets.count_documents({"status": "New"})

    return OverviewStats(
        active_patients=len(active_patient_ids),
        sessions_today=sessions_today,
        reminders_sent_today=reminders_today,
        pending_codes=pending_codes,
        new_forgot_requests=new_forgot,
    )


@router.get("/activity", response_model=List[ActivityItem])
async def get_activity(
    limit: int = 20,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """Recent system activity — merged from sessions, reminders, support_tickets."""
    events: List[Dict[str, Any]] = []

    # Recent sessions
    async for s in db.db.sessions.find(
        {}, {"patient_id": 1, "created_at": 1, "active": 1}
    ).sort("created_at", -1).limit(limit):
        events.append({
            "ts": s.get("created_at", datetime.utcnow()),
            "type": "New Session",
            "patient": s.get("patient_id", "Unknown"),
            "status": "Active" if s.get("active") else "Completed",
        })

    # Recent reminders
    async for r in db.db.reminder_logs.find(
        {}, {"patient_name": 1, "sent_at": 1, "status": 1}
    ).sort("sent_at", -1).limit(limit):
        events.append({
            "ts": r.get("sent_at", datetime.utcnow()),
            "type": "Reminder Sent",
            "patient": r.get("patient_name", "Unknown"),
            "status": r.get("status", "Pending"),
        })

    # Recent code activations (first login)
    async for c in db.db.patient_codes.find(
        {"first_login_at": {"$ne": None}},
        {"patient_name": 1, "first_login_at": 1}
    ).sort("first_login_at", -1).limit(10):
        events.append({
            "ts": c.get("first_login_at", datetime.utcnow()),
            "type": "Code Activated",
            "patient": c.get("patient_name", "Unknown"),
            "status": "Delivered",
        })

    # Sort all events by time desc, take top `limit`
    events.sort(key=lambda e: e["ts"], reverse=True)
    events = events[:limit]

    return [
        ActivityItem(
            time=e["ts"].strftime("%I:%M %p"),
            type=e["type"],
            patient=e["patient"],
            status=e["status"],
        )
        for e in events
    ]


@router.get("/system-status", response_model=List[SystemService])
async def get_system_status(
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Check health of system components."""
    results: List[SystemService] = []

    # Backend API — always operational if this endpoint responds
    results.append(SystemService(name="Backend API", status="Operational"))

    # MongoDB
    try:
        await db.client.admin.command("ping", serverSelectionTimeoutMS=2000)
        results.append(SystemService(name="MongoDB", status="Operational"))
    except Exception:
        results.append(SystemService(name="MongoDB", status="Down"))

    # Medical Doc RAG (check flag in settings)
    if settings.MEDICAL_DOC_RAG_ENABLED:
        results.append(SystemService(name="Medical Doc RAG", status="Operational"))
    else:
        results.append(SystemService(name="Medical Doc RAG", status="Degraded"))

    # Ollama / MedGemma
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                results.append(SystemService(name="MedGemma LLM", status="Operational"))
            else:
                results.append(SystemService(name="MedGemma LLM", status="Degraded"))
    except Exception:
        results.append(SystemService(name="MedGemma LLM", status="Down"))

    return results


# ─── Patients ────────────────────────────────────────────────────────────────

@router.get("/patients", response_model=List[PatientOut])
async def list_patients(
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """
    List all patients that have an entry in patient_codes collection.
    Sessions are used to derive activity metrics.
    """
    patients: List[PatientOut] = []

    async for code in db.db.patient_codes.find({}).sort("issued_at", -1):
        pid = code["patient_id"]
        patient_name = code.get("patient_name", "Unknown")

        # Count sessions for this patient
        session_count = await db.db.sessions.count_documents({"patient_id": pid})

        # Last session
        last_sess = await db.db.sessions.find_one(
            {"patient_id": pid},
            sort=[("created_at", -1)]
        )
        last_session_str = _relative_time(
            last_sess.get("created_at") if last_sess else None
        )

        # Determine status
        if code.get("status") == "Revoked":
            pat_status = "Inactive"
        elif code.get("first_login_at"):
            pat_status = "Active"
        else:
            pat_status = "Pending"

        # Consent: consented = has completed first login
        consented = bool(code.get("first_login_at"))
        consent_date = ""
        if consented and code.get("first_login_at"):
            consent_date = code["first_login_at"].strftime("%b %d")

        patients.append(PatientOut(
            id=pid,
            name=patient_name,
            status=pat_status,
            consented=consented,
            consent_date=consent_date,
            last_session=last_session_str if session_count > 0 else "Never",
            sessions=session_count,
            email=code.get("email"),
            phone=code.get("phone"),
        ))

    return patients


@router.post("/patients", response_model=PatientOut, status_code=201)
async def create_patient(
    req: CreatePatientRequest,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """
    Register a new patient.
    Creates a patient_codes document with status=Active.
    The patient_id IS the login code (FirstName###_LastName###_uuid).

    NOTE: Does NOT modify FHIR data. Only creates an admin-managed record.
    """
    # Parse name to build patient_id
    parts = req.name.strip().split()
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Full name required (first and last)")

    import re, random
    first = re.sub(r"[^A-Za-z]", "", parts[0])
    last = re.sub(r"[^A-Za-z]", "", parts[-1])
    num1 = random.randint(100, 999)
    num2 = random.randint(100, 999)
    new_uuid = str(uuid.uuid4())
    patient_id = f"{first.capitalize()}{num1}_{last.capitalize()}{num2}_{new_uuid}"

    doc = {
        "patient_id": patient_id,
        "patient_name": req.name.strip(),
        "email": req.email,
        "phone": req.phone,
        "status": "Active",
        "issued_at": datetime.utcnow(),
        "first_login_at": None,
    }
    await db.db.patient_codes.insert_one(doc)
    logger.info(f"Admin created patient: {patient_id}")

    return PatientOut(
        id=patient_id,
        name=req.name.strip(),
        status="Pending",
        consented=False,
        consent_date="",
        last_session="Never",
        sessions=0,
        email=req.email,
        phone=req.phone,
    )


# ─── Patient Codes ────────────────────────────────────────────────────────────

@router.get("/patient-codes", response_model=List[PatientCodeOut])
async def list_patient_codes(
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """List all patient login codes and their activation status."""
    codes: List[PatientCodeOut] = []
    async for doc in db.db.patient_codes.find({}).sort("issued_at", -1):
        codes.append(PatientCodeOut(
            patient_id=doc["patient_id"],
            patient_name=doc.get("patient_name", "Unknown"),
            issued_at=_fmt_time(doc.get("issued_at")),
            status=doc.get("status", "Active"),
            first_login_at=_fmt_time(doc.get("first_login_at")) if doc.get("first_login_at") else None,
        ))
    return codes


@router.patch("/patient-codes/{patient_id}/revoke", status_code=204)
async def revoke_patient_code(
    patient_id: str,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """Revoke a patient's login code. Existing sessions remain valid until expiry."""
    result = await db.db.patient_codes.update_one(
        {"patient_id": patient_id},
        {"$set": {"status": "Revoked", "revoked_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient code not found")
    logger.info(f"Admin revoked patient code: {patient_id}")


# ─── Medications ─────────────────────────────────────────────────────────────

@router.get("/medications", response_model=List[MedicationOut])
async def list_medications(
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """List all medication reminder schedules."""
    meds: List[MedicationOut] = []
    async for doc in db.db.medications.find({}).sort("created_at", -1):
        meds.append(MedicationOut(
            id=str(doc["_id"]),
            patient_id=doc.get("patient_id", ""),
            patient_name=doc.get("patient_name", "Unknown"),
            medication=doc.get("medication", ""),
            dosage=doc.get("dosage", ""),
            frequency=doc.get("frequency", ""),
            times=doc.get("times", []),
            start_date=doc.get("start_date", ""),
            end_date=doc.get("end_date"),
            reminders_sent=doc.get("reminders_sent", 0),
            reminders_total=doc.get("reminders_total", 0),
            status=doc.get("status", "Active"),
        ))
    return meds


@router.post("/medications", response_model=MedicationOut, status_code=201)
async def create_medication(
    req: CreateMedicationRequest,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """Create a new medication reminder schedule for a patient."""
    from bson import ObjectId
    doc = {
        "patient_id": req.patient_id,
        "patient_name": req.patient_name,
        "medication": req.medication,
        "dosage": req.dosage,
        "frequency": req.frequency,
        "times": req.times,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "patient_email": req.patient_email,
        "notes": req.notes,
        "reminders_sent": 0,
        "reminders_total": len(req.times) * 30,  # estimate: 30 days
        "status": "Active",
        "created_at": datetime.utcnow(),
    }
    result = await db.db.medications.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info(f"Admin created medication schedule for {req.patient_name}")

    return MedicationOut(
        id=str(result.inserted_id),
        patient_id=req.patient_id,
        patient_name=req.patient_name,
        medication=req.medication,
        dosage=req.dosage,
        frequency=req.frequency,
        times=req.times,
        start_date=req.start_date,
        end_date=req.end_date,
        reminders_sent=0,
        reminders_total=len(req.times) * 30,
        status="Active",
    )


@router.patch("/medications/{med_id}/status", status_code=204)
async def update_medication_status(
    med_id: str,
    req: UpdateStatusRequest,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """Pause, resume, or complete a medication schedule."""
    from bson import ObjectId
    allowed = {"Active", "Paused", "Completed"}
    if req.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {allowed}")
    result = await db.db.medications.update_one(
        {"_id": ObjectId(med_id)},
        {"$set": {"status": req.status, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Medication schedule not found")


@router.delete("/medications/{med_id}", status_code=204)
async def delete_medication(
    med_id: str,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """Delete a medication schedule permanently."""
    from bson import ObjectId
    result = await db.db.medications.delete_one({"_id": ObjectId(med_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Medication schedule not found")
    logger.info(f"Admin deleted medication schedule: {med_id}")


# ─── Reminder Logs ────────────────────────────────────────────────────────────

@router.get("/reminder-logs", response_model=List[ReminderLogOut])
async def list_reminder_logs(
    limit: int = 100,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """List recent email reminder delivery logs."""
    logs: List[ReminderLogOut] = []
    async for doc in db.db.reminder_logs.find({}).sort("sent_at", -1).limit(limit):
        logs.append(ReminderLogOut(
            id=str(doc["_id"]),
            sent_at=_fmt_time(doc.get("sent_at")),
            patient_name=doc.get("patient_name", "Unknown"),
            medication=doc.get("medication", ""),
            email_masked=doc.get("email_masked", "***"),
            status=doc.get("status", "Pending"),
            error=doc.get("error"),
        ))
    return logs


# ─── Forgot ID Requests ───────────────────────────────────────────────────────

@router.get("/forgot-id-requests", response_model=List[ForgotRequestOut])
async def list_forgot_requests(
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """List all patient 'Forgot ID' support tickets."""
    requests: List[ForgotRequestOut] = []
    async for doc in db.db.support_tickets.find(
        {"type": "forgot_id"}
    ).sort("submitted_at", -1):
        requests.append(ForgotRequestOut(
            id=doc.get("ticket_id", str(doc["_id"])),
            submitted_at=_fmt_time(doc.get("submitted_at")),
            name=doc.get("name", ""),
            dob=doc.get("dob", ""),
            phone=doc.get("phone", ""),
            email=doc.get("email", ""),
            visit_date=doc.get("visit_date", ""),
            department=doc.get("department", ""),
            notes=doc.get("notes", ""),
            status=doc.get("status", "New"),
        ))
    return requests


@router.patch("/forgot-id-requests/{ticket_id}/status", status_code=204)
async def update_forgot_request_status(
    ticket_id: str,
    req: UpdateStatusRequest,
    _: str = Depends(verify_admin),
    db: Database = Depends(get_db),
):
    """Update the status of a Forgot ID support ticket."""
    allowed = {"New", "In Progress", "Resolved"}
    if req.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {allowed}")
    result = await db.db.support_tickets.update_one(
        {"ticket_id": ticket_id, "type": "forgot_id"},
        {"$set": {"status": req.status, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    logger.info(f"Admin updated ticket {ticket_id} → {req.status}")
