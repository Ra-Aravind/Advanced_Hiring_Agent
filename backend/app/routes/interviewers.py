import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interviewer import Interviewer
from app.models.user import User
from app.schemas.interviewer import InterviewerCreate, InterviewerOut, InterviewerDetailed

router = APIRouter()


# ── GET — Detailed list with name/email from Users ────────────────────────────

@router.get("/detailed", response_model=list[InterviewerDetailed])
def get_interviewers_detailed(db: Session = Depends(get_db)):
    """Return all interviewers enriched with name and email from Users table."""
    rows = (
        db.query(Interviewer, User)
        .join(User, Interviewer.user_id == User.user_id)
        .all()
    )
    result = []
    for interviewer, user in rows:
        result.append(InterviewerDetailed(
            interviewer_id=interviewer.interviewer_id,
            name=user.name,
            email=user.email,
            department=interviewer.department,
            expertise=interviewer.expertise,
            availability_status=interviewer.availability_status,
            experience_years=float(interviewer.experience_years) if interviewer.experience_years else None,
        ))
    return result


# ── GET — All (basic) ─────────────────────────────────────────────────────────

@router.get("", response_model=list[InterviewerOut])
def get_interviewers(db: Session = Depends(get_db)):
    return db.query(Interviewer).all()


# ── GET — Single ──────────────────────────────────────────────────────────────

@router.get("/{interviewer_id}", response_model=InterviewerOut)
def get_interviewer(interviewer_id: str, db: Session = Depends(get_db)):
    interviewer = db.get(Interviewer, interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return interviewer


# ── GET — Availability ───────────────────────────────────────────────────────

@router.get("/{interviewer_id}/availability")
def get_availability(interviewer_id: str, db: Session = Depends(get_db)):
    interviewer = db.get(Interviewer, interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return {"interviewer_id": interviewer_id, "availability_status": interviewer.availability_status}


# ── PATCH — Update Availability ───────────────────────────────────────────────

@router.patch("/{interviewer_id}/availability")
def update_availability(
    interviewer_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    interviewer = db.get(Interviewer, interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    status = payload.get("availability_status")
    if status not in ("AVAILABLE", "BUSY"):
        raise HTTPException(status_code=400, detail="availability_status must be AVAILABLE or BUSY")
    interviewer.availability_status = status
    db.commit()
    db.refresh(interviewer)
    return {"interviewer_id": interviewer_id, "availability_status": interviewer.availability_status}


# ── POST — Add New Interviewer ────────────────────────────────────────────────

@router.post("", response_model=InterviewerDetailed)
def create_interviewer(payload: InterviewerCreate, db: Session = Depends(get_db)):
    """
    Add a new interviewer. Creates both a User row and an Interviewer row.
    """
    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=f"A user with email '{payload.email}' already exists."
        )

    # Generate IDs
    uid_suffix = uuid.uuid4().hex[:6].upper()
    user_id = f"U-INTV-{uid_suffix}"
    interviewer_id = f"INTV-{uid_suffix}"

    # Create User
    user = User(
        user_id=user_id,
        name=payload.name,
        email=payload.email,
        role="INTERVIEWER",
        status="ACTIVE",
    )
    db.add(user)
    db.flush()

    # Create Interviewer
    interviewer = Interviewer(
        interviewer_id=interviewer_id,
        user_id=user_id,
        department=payload.department,
        experience_years=payload.experience_years,
        expertise=payload.expertise,
        availability_status=payload.availability_status,
    )
    db.add(interviewer)
    db.commit()
    db.refresh(interviewer)

    return InterviewerDetailed(
        interviewer_id=interviewer.interviewer_id,
        name=user.name,
        email=user.email,
        department=interviewer.department,
        expertise=interviewer.expertise,
        availability_status=interviewer.availability_status,
        experience_years=float(interviewer.experience_years) if interviewer.experience_years else None,
    )


# ── DELETE — Remove Interviewer ───────────────────────────────────────────────

@router.delete("/{interviewer_id}")
def delete_interviewer(interviewer_id: str, db: Session = Depends(get_db)):
    """
    Remove an interviewer. Prevents deletion if they have scheduled interviews.
    """
    from app.models.interview import Interview

    interviewer = db.get(Interviewer, interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    # Safety check: do not delete if they have active scheduled interviews
    active_interviews = (
        db.query(Interview)
        .filter(
            Interview.interviewer_id == interviewer_id,
            Interview.status.in_(["SCHEDULED", "IN_PROGRESS"])
        )
        .count()
    )

    if active_interviews > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove interviewer — they have {active_interviews} active interview(s). Cancel them first."
        )

    # Also remove the User row
    user = db.get(User, interviewer.user_id)

    db.delete(interviewer)
    if user and user.role == "INTERVIEWER":
        db.delete(user)

    db.commit()

    return {"message": f"Interviewer {interviewer_id} removed successfully."}