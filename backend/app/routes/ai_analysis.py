from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview
from app.models.feedback import InterviewFeedback
from app.models.candidate import Candidate
from app.models.user import User
from app.services.ai_service import analyze_interview_feedback

router = APIRouter()

@router.post("/{interview_id}/analyze")
def run_ai_analysis(interview_id: str, db: Session = Depends(get_db)):
    # 1. Load Interview
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    # 2. Load Feedback
    feedback = db.query(InterviewFeedback).filter(
        InterviewFeedback.interview_id == interview_id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=400, detail="Cannot analyze without feedback. Submit feedback first.")
        
    # 3. Load Candidate Data
    candidate = db.get(Candidate, interview.candidate_id)
    cand_user = db.get(User, candidate.user_id) if candidate else None
    
    # 4. Call AI Service
    analysis = analyze_interview_feedback(
        interview_id=interview_id,
        candidate_name=cand_user.name if cand_user else "Unknown",
        candidate_skill=candidate.primary_skill if candidate else "Unknown",
        interview_type=interview.interview_type,
        phase1_score=float(candidate.phase1_score) if candidate and candidate.phase1_score else 0.0,
        technical_score=float(feedback.technical_score),
        problem_solving_score=float(feedback.problem_solving_score),
        communication_score=float(feedback.communication_score),
        coding_score=float(feedback.coding_score),
        confidence_score=float(feedback.confidence_score),
        overall_score=float(feedback.overall_score),
        strengths=feedback.strengths or "",
        weaknesses=feedback.weaknesses or "",
        technical_comments=feedback.technical_comments or "",
        interviewer_recommendation=feedback.recommendation or "HOLD",
    )
    
    return analysis
