from datetime import date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InterviewCreate(BaseModel):
    # interview_id is now optional — server auto-generates if not provided
    interview_id: Optional[str] = None

    candidate_id: str
    interviewer_id: str
    recruiter_id: str = "U-REC-01"   # defaults to system recruiter

    interview_type: str = "TECHNICAL"
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = Field(default=45, ge=15, le=180)
    platform: str = "JITSI_MEET"


class InterviewOut(BaseModel):
    interview_id: str
    candidate_id: str
    interviewer_id: str
    recruiter_id: str
    interview_type: str
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int
    platform: str
    meeting_id: Optional[str] = None
    meeting_link: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class InterviewDetailed(BaseModel):
    """Interview enriched with candidate and interviewer names."""
    interview_id: str
    interview_type: str
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int
    platform: str
    meeting_link: Optional[str] = None
    status: str

    # Candidate info
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_skill: Optional[str] = None
    phase1_score: Optional[float] = None

    # Interviewer info
    interviewer_id: str
    interviewer_name: str
    interviewer_email: str

    model_config = ConfigDict(from_attributes=True)


class InterviewStatusUpdate(BaseModel):
    status: str