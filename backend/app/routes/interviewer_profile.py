"""
Interviewer Profile Route
Returns everything an interviewer needs on their personal dashboard:
- Their own details
- Candidates allocated to them (via interviews)
- Candidate Phase 1 assessment scores
- Feedback they've submitted
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.interviewer import Interviewer
from app.models.interview import Interview
from app.models.candidate import Candidate
from app.models.user import User
from app.models.feedback import InterviewFeedback

router = APIRouter()


class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    email: str
    primary_skill: Optional[str] = None
    phase1_score: Optional[float] = None
    phase1_status: Optional[str] = None
    experience_years: Optional[float] = None

    # Interview details
    interview_id: str
    interview_type: str
    scheduled_date: str
    scheduled_time: str
    duration_minutes: int
    meeting_link: Optional[str] = None
    interview_status: str
    platform: str

    # Feedback (if submitted)
    has_feedback: bool = False
    technical_score: Optional[float] = None
    problem_solving_score: Optional[float] = None
    communication_score: Optional[float] = None
    coding_score: Optional[float] = None
    confidence_score: Optional[float] = None
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    technical_comments: Optional[str] = None


class InterviewerProfileResponse(BaseModel):
    interviewer_id: str
    name: str
    email: str
    department: Optional[str] = None
    expertise: Optional[str] = None
    experience_years: Optional[float] = None
    availability_status: str
    total_interviews: int
    completed_interviews: int
    pending_feedback: int
    allocated_candidates: List[CandidateProfile]


@router.get("/{interviewer_id}/profile", response_model=InterviewerProfileResponse)
def get_interviewer_profile(interviewer_id: str, db: Session = Depends(get_db)):
    """
    Returns the full profile of an interviewer including all their
    allocated candidates, Phase 1 scores, and any submitted feedback.
    """
    # 1. Load interviewer
    interviewer = db.get(Interviewer, interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    user = db.get(User, interviewer.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Interviewer user not found")

    # 2. Load all interviews assigned to this interviewer
    interviews = (
        db.query(Interview)
        .filter(Interview.interviewer_id == interviewer_id)
        .order_by(Interview.scheduled_date, Interview.scheduled_time)
        .all()
    )

    allocated_candidates = []

    for iv in interviews:
        candidate = db.get(Candidate, iv.candidate_id)
        if not candidate:
            continue

        cand_user = db.get(User, candidate.user_id)
        if not cand_user:
            continue

        # Load feedback for this interview
        feedback = (
            db.query(InterviewFeedback)
            .filter(InterviewFeedback.interview_id == iv.interview_id)
            .first()
        )

        cp = CandidateProfile(
            candidate_id=candidate.candidate_id,
            name=cand_user.name,
            email=cand_user.email,
            primary_skill=candidate.primary_skill,
            phase1_score=float(candidate.phase1_score) if candidate.phase1_score else None,
            phase1_status=candidate.phase1_status,
            experience_years=float(candidate.experience_years) if candidate.experience_years else None,
            interview_id=iv.interview_id,
            interview_type=iv.interview_type,
            scheduled_date=str(iv.scheduled_date),
            scheduled_time=str(iv.scheduled_time),
            duration_minutes=iv.duration_minutes,
            meeting_link=iv.meeting_link,
            interview_status=iv.status,
            platform=iv.platform,
            has_feedback=feedback is not None,
            technical_score=float(feedback.technical_score) if feedback and feedback.technical_score else None,
            problem_solving_score=float(feedback.problem_solving_score) if feedback and feedback.problem_solving_score else None,
            communication_score=float(feedback.communication_score) if feedback and feedback.communication_score else None,
            coding_score=float(feedback.coding_score) if feedback and feedback.coding_score else None,
            confidence_score=float(feedback.confidence_score) if feedback and feedback.confidence_score else None,
            overall_score=float(feedback.overall_score) if feedback and feedback.overall_score else None,
            recommendation=feedback.recommendation if feedback else None,
            strengths=feedback.strengths if feedback else None,
            weaknesses=feedback.weaknesses if feedback else None,
            technical_comments=feedback.technical_comments if feedback else None,
        )
        allocated_candidates.append(cp)

    total = len(interviews)
    completed = sum(1 for iv in interviews if iv.status == "COMPLETED")
    pending_fb = sum(1 for iv in interviews if iv.status == "COMPLETED" and
                     not db.query(InterviewFeedback).filter(InterviewFeedback.interview_id == iv.interview_id).first())

    return InterviewerProfileResponse(
        interviewer_id=interviewer.interviewer_id,
        name=user.name,
        email=user.email,
        department=interviewer.department,
        expertise=interviewer.expertise,
        experience_years=float(interviewer.experience_years) if interviewer.experience_years else None,
        availability_status=interviewer.availability_status,
        total_interviews=total,
        completed_interviews=completed,
        pending_feedback=pending_fb,
        allocated_candidates=allocated_candidates,
    )


@router.get("/by-email/{email}", response_model=InterviewerProfileResponse)
def get_interviewer_profile_by_email(email: str, db: Session = Depends(get_db)):
    """Lookup interviewer by email address (used after login to find their profile)."""
    user = db.query(User).filter(User.email == email, User.role == "INTERVIEWER").first()
    if not user:
        raise HTTPException(status_code=404, detail="Interviewer not found for this email")

    interviewer = db.query(Interviewer).filter(Interviewer.user_id == user.user_id).first()
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer profile not found")

    return get_interviewer_profile(interviewer.interviewer_id, db)
