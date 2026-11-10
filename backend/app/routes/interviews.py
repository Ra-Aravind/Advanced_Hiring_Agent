import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview
from app.models.candidate import Candidate
from app.models.interviewer import Interviewer
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate,
    InterviewOut,
    InterviewDetailed,
    InterviewStatusUpdate,
)
from app.services.interview_service import has_schedule_conflict

router = APIRouter()

ALLOWED_STATUSES = ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW", "PENDING_FEEDBACK"]


def _generate_interview_id() -> str:
    """Auto-generate a short interview ID like INT-2026-A3F9."""
    suffix = uuid.uuid4().hex[:6].upper()
    year = datetime.now().year
    return f"INT-{year}-{suffix}"


# ── POST — Create Interview ───────────────────────────────────────────────────

@router.post("", response_model=InterviewOut)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db)):

    # Auto-generate ID if not provided
    interview_id = payload.interview_id or _generate_interview_id()

    # 1. Check candidate exists
    candidate = db.get(Candidate, payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 2. Check eligibility
    if not candidate.interview_eligible:
        raise HTTPException(status_code=400, detail="Candidate is not eligible for interview")

    # 3. Check interviewer exists
    interviewer = db.get(Interviewer, payload.interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    # 4. Check interviewer availability
    if interviewer.availability_status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Interviewer is currently unavailable")

    # 5. Check schedule conflict
    if has_schedule_conflict(
        db=db,
        interviewer_id=payload.interviewer_id,
        scheduled_date=payload.scheduled_date,
        scheduled_time=payload.scheduled_time,
        duration_minutes=payload.duration_minutes,
    ):
        raise HTTPException(status_code=409, detail="Interviewer has a conflicting interview at this time")

    # 6. Check duplicate ID
    if db.get(Interview, interview_id):
        raise HTTPException(status_code=409, detail="Interview ID already exists")

    # 7. Create
    interview = Interview(
        interview_id=interview_id,
        candidate_id=payload.candidate_id,
        interviewer_id=payload.interviewer_id,
        recruiter_id=payload.recruiter_id,
        interview_type=payload.interview_type,
        scheduled_date=payload.scheduled_date,
        scheduled_time=payload.scheduled_time,
        duration_minutes=payload.duration_minutes,
        platform=payload.platform,
        status="SCHEDULED",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


# ── GET — List All (basic) ────────────────────────────────────────────────────

@router.get("", response_model=list[InterviewOut])
def get_interviews(db: Session = Depends(get_db)):
    return (
        db.query(Interview)
        .order_by(Interview.scheduled_date, Interview.scheduled_time)
        .all()
    )


# ── GET — Detailed list with names ───────────────────────────────────────────

@router.get("/detailed", response_model=list[InterviewDetailed])
def get_interviews_detailed(db: Session = Depends(get_db)):
    """Return interviews with candidate and interviewer names joined from Users."""
    CandUser = User.__table__.alias("cand_user")
    IntvUser = User.__table__.alias("intv_user")

    rows = (
        db.query(Interview, Candidate, Interviewer)
        .join(Candidate, Interview.candidate_id == Candidate.candidate_id)
        .join(Interviewer, Interview.interviewer_id == Interviewer.interviewer_id)
        .order_by(Interview.scheduled_date, Interview.scheduled_time)
        .all()
    )

    result = []
    for interview, candidate, interviewer in rows:
        cand_user = db.get(User, candidate.user_id)
        intv_user = db.get(User, interviewer.user_id)
        result.append(InterviewDetailed(
            interview_id=interview.interview_id,
            interview_type=interview.interview_type,
            scheduled_date=interview.scheduled_date,
            scheduled_time=interview.scheduled_time,
            duration_minutes=interview.duration_minutes,
            platform=interview.platform,
            meeting_link=interview.meeting_link,
            status=interview.status,
            candidate_id=candidate.candidate_id,
            candidate_name=cand_user.name if cand_user else "Unknown",
            candidate_email=cand_user.email if cand_user else "",
            candidate_skill=candidate.primary_skill,
            phase1_score=float(candidate.phase1_score) if candidate.phase1_score else None,
            interviewer_id=interviewer.interviewer_id,
            interviewer_name=intv_user.name if intv_user else "Unknown",
            interviewer_email=intv_user.email if intv_user else "",
        ))
    return result


# ── GET — Single Interview ───────────────────────────────────────────────────

@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(interview_id: str, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


# ── PATCH — Update Status ────────────────────────────────────────────────────

@router.patch("/{interview_id}/status", response_model=InterviewOut)
def update_interview_status(
    interview_id: str,
    payload: InterviewStatusUpdate,
    db: Session = Depends(get_db),
):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {ALLOWED_STATUSES}")
    interview.status = payload.status
    db.commit()
    db.refresh(interview)
    return interview


# ── DELETE — Cancel Interview ─────────────────────────────────────────────────

@router.delete("/{interview_id}")
def delete_interview(interview_id: str, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status in ("COMPLETED",):
        raise HTTPException(status_code=400, detail="Cannot delete a completed interview")
    interview.status = "CANCELLED"
    db.commit()
    return {"message": f"Interview {interview_id} cancelled successfully"}