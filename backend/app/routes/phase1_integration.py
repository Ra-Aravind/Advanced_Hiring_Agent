import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.user import User

router = APIRouter()

class Phase1Result(BaseModel):
    name: str
    email: str
    technology: str
    score: float
    status: str
    interview_eligible: bool


@router.post("/assessment-result")
def receive_phase1_result(payload: Phase1Result, db: Session = Depends(get_db)):
    """
    Webhook endpoint for Phase 1 to send assessment results.
    Creates or updates the User and Candidate records in Phase 2.
    """
    
    # 1. Handle User
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user_id = f"U-CAND-{uuid.uuid4().hex[:6].upper()}"
        user = User(
            user_id=user_id,
            name=payload.name,
            email=payload.email,
            role="CANDIDATE",
            status="ACTIVE"
        )
        db.add(user)
        db.flush() # flush to get the user added in transaction

    # 2. Handle Candidate
    candidate = db.query(Candidate).filter(Candidate.user_id == user.user_id).first()
    if not candidate:
        candidate_id = f"CAND-{uuid.uuid4().hex[:6].upper()}"
        candidate = Candidate(
            candidate_id=candidate_id,
            user_id=user.user_id,
            primary_skill=payload.technology,
            phase1_score=payload.score,
            phase1_status=payload.status,
            interview_eligible=payload.interview_eligible,
        )
        db.add(candidate)
    else:
        # Update existing candidate
        candidate.primary_skill = payload.technology
        candidate.phase1_score = payload.score
        candidate.phase1_status = payload.status
        candidate.interview_eligible = payload.interview_eligible

    db.commit()
    
    return {
        "message": "Phase 1 result successfully imported to Phase 2",
        "candidate_id": candidate.candidate_id,
        "interview_eligible": candidate.interview_eligible
    }
