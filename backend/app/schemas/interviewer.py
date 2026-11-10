from typing import Optional
from pydantic import BaseModel, ConfigDict

class InterviewerCreate(BaseModel):
    name: str
    email: str
    department: Optional[str] = None
    experience_years: Optional[float] = None
    expertise: Optional[str] = None
    availability_status: str = "AVAILABLE"

class InterviewerOut(BaseModel):
    interviewer_id: str
    user_id: str
    department: Optional[str] = None
    experience_years: Optional[float] = None
    expertise: Optional[str] = None
    availability_status: str

    model_config = ConfigDict(from_attributes=True)


class InterviewerDetailed(BaseModel):
    """Interviewer enriched with User name and email."""
    interviewer_id: str
    name: str
    email: str
    department: Optional[str] = None
    expertise: Optional[str] = None
    availability_status: str
    experience_years: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)