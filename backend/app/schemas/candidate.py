from typing import Optional
from pydantic import BaseModel, ConfigDict


class CandidateCreate(BaseModel):
    candidate_id: str
    user_id: str
    primary_skill: Optional[str] = None
    phase1_assessment_id: Optional[str] = None
    phase1_score: Optional[float] = None
    phase1_status: Optional[str] = None
    interview_eligible: bool = False
    experience_years: Optional[float] = None


class CandidateOut(CandidateCreate):
    model_config = ConfigDict(from_attributes=True)


class CandidateDetailed(BaseModel):
    """Candidate enriched with User name and email."""
    candidate_id: str
    name: str
    email: str
    primary_skill: Optional[str] = None
    phase1_score: Optional[float] = None
    phase1_status: Optional[str] = None
    interview_eligible: bool
    experience_years: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)