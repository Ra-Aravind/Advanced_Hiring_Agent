from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview
from app.models.candidate import Candidate
from app.models.interviewer import Interviewer
from app.models.user import User
from app.services.meeting_service import generate_meeting_link
from app.services.email_service import send_interview_emails

router = APIRouter()


@router.post("/{interview_id}/create")
def create_meeting(interview_id: str, db: Session = Depends(get_db)):
    """
    Generate a Jitsi Meet link for the interview and send email
    notifications to both the candidate and interviewer.
    """
    # 1. Load interview
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot create meeting for a cancelled interview")

    # 2. Load candidate + user info
    candidate = db.get(Candidate, interview.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    cand_user = db.get(User, candidate.user_id)

    # 3. Load interviewer + user info
    interviewer = db.get(Interviewer, interview.interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    intv_user = db.get(User, interviewer.user_id)

    # 4. Generate Jitsi link
    meeting_data = generate_meeting_link(
        interview_id=interview_id,
        scheduled_date=interview.scheduled_date,
    )

    # 5. Store in database
    interview.meeting_id = meeting_data["meeting_id"]
    interview.meeting_link = meeting_data["meeting_link"]
    interview.platform = "JITSI_MEET"
    db.commit()

    # 6. Format display values for emails
    interview_date = str(interview.scheduled_date)
    interview_time = str(interview.scheduled_time)[:5]   # HH:MM

    # 7. Send emails
    email_result = send_interview_emails(
        candidate_name=cand_user.name if cand_user else "Candidate",
        candidate_email=cand_user.email if cand_user else "",
        interviewer_name=intv_user.name if intv_user else "Interviewer",
        interviewer_email=intv_user.email if intv_user else "",
        candidate_skill=candidate.primary_skill or "N/A",
        phase1_score=float(candidate.phase1_score) if candidate.phase1_score else 0,
        interview_date=interview_date,
        interview_time=interview_time,
        duration_minutes=interview.duration_minutes,
        interview_type=interview.interview_type,
        meeting_link=meeting_data["meeting_link"],
    )

    return {
        "interview_id": interview_id,
        "platform": "JITSI_MEET",
        "meeting_id": meeting_data["meeting_id"],
        "meeting_link": meeting_data["meeting_link"],
        "emails": email_result,
        "message": "Meeting created successfully. Notifications sent to candidate and interviewer.",
    }
