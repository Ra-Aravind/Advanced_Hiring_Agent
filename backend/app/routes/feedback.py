import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import InterviewFeedback
from app.models.interview import Interview
from app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter()


@router.post("/{interview_id}", response_model=FeedbackOut)
def submit_feedback(
    interview_id: str,
    payload: FeedbackCreate,
    db: Session = Depends(get_db)
):
    # 1. Ensure interview exists
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # 2. Check if feedback already exists — UPSERT (update instead of error)
    existing_feedback = db.query(InterviewFeedback).filter(
        InterviewFeedback.interview_id == interview_id
    ).first()

    if existing_feedback:
        # Update all fields on the existing record
        existing_feedback.interviewer_id = payload.interviewer_id
        existing_feedback.technical_score = payload.technical_score
        existing_feedback.problem_solving_score = payload.problem_solving_score
        existing_feedback.communication_score = payload.communication_score
        existing_feedback.coding_score = payload.coding_score
        existing_feedback.confidence_score = payload.confidence_score
        existing_feedback.overall_score = payload.overall_score
        existing_feedback.strengths = payload.strengths
        existing_feedback.weaknesses = payload.weaknesses
        existing_feedback.technical_comments = payload.technical_comments
        existing_feedback.recommendation = payload.recommendation

        interview.status = "COMPLETED"
        db.commit()
        db.refresh(existing_feedback)
        return existing_feedback

    # 3. Create new feedback record
    feedback_id = f"FB-{uuid.uuid4().hex[:8].upper()}"

    feedback = InterviewFeedback(
        feedback_id=feedback_id,
        interview_id=interview_id,
        **payload.model_dump()
    )

    db.add(feedback)

    # 4. Mark interview as COMPLETED
    interview.status = "COMPLETED"

    db.commit()
    db.refresh(feedback)

    return feedback


@router.get("/{interview_id}", response_model=FeedbackOut)
def get_feedback(interview_id: str, db: Session = Depends(get_db)):
    feedback = db.query(InterviewFeedback).filter(
        InterviewFeedback.interview_id == interview_id
    ).first()

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found for this interview")

    return feedback


@router.delete("/{interview_id}")
def delete_feedback(interview_id: str, db: Session = Depends(get_db)):
    feedback = db.query(InterviewFeedback).filter(
        InterviewFeedback.interview_id == interview_id
    ).first()

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    db.delete(feedback)

    # Reset interview status so it can be re-evaluated
    interview = db.get(Interview, interview_id)
    if interview:
        interview.status = "COMPLETED"

    db.commit()

    return {"message": "Feedback deleted. You can now resubmit."}
