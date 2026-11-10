from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    interviewer_id: str

    technical_score: float = Field(ge=0, le=10)
    problem_solving_score: float = Field(ge=0, le=10)
    communication_score: float = Field(ge=0, le=10)
    coding_score: float = Field(ge=0, le=10)
    confidence_score: float = Field(ge=0, le=10)
    overall_score: float = Field(ge=0, le=10)

    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    technical_comments: Optional[str] = None

    recommendation: str   # HIRE | HOLD | REJECT


class FeedbackOut(BaseModel):
    feedback_id: str
    interview_id: str
    interviewer_id: str

    technical_score: Optional[float] = None
    problem_solving_score: Optional[float] = None
    communication_score: Optional[float] = None
    coding_score: Optional[float] = None
    confidence_score: Optional[float] = None
    overall_score: Optional[float] = None

    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    technical_comments: Optional[str] = None
    recommendation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
