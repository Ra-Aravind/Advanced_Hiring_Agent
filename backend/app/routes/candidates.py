from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate import CandidateCreate, CandidateOut, CandidateDetailed

router = APIRouter()


@router.get("/detailed", response_model=list[CandidateDetailed])
def get_candidates_detailed(db: Session = Depends(get_db)):
    """Return all candidates enriched with name and email from Users table."""
    rows = (
        db.query(Candidate, User)
        .join(User, Candidate.user_id == User.user_id)
        .all()
    )
    result = []
    for candidate, user in rows:
        result.append(CandidateDetailed(
            candidate_id=candidate.candidate_id,
            name=user.name,
            email=user.email,
            primary_skill=candidate.primary_skill,
            phase1_score=float(candidate.phase1_score) if candidate.phase1_score else None,
            phase1_status=candidate.phase1_status,
            interview_eligible=candidate.interview_eligible,
            experience_years=float(candidate.experience_years) if candidate.experience_years else None,
        ))
    return result


@router.get("", response_model=list[CandidateOut])
def get_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).all()


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("", response_model=CandidateOut)
def create_candidate(candidate_data: CandidateCreate, db: Session = Depends(get_db)):
    existing = db.get(Candidate, candidate_data.candidate_id)
    if existing:
        raise HTTPException(status_code=409, detail="Candidate already exists")
    candidate = Candidate(**candidate_data.model_dump())
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate