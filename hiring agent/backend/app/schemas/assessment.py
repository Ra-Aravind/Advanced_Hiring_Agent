from pydantic import BaseModel, field_validator
from typing import Optional, Dict, List
from datetime import datetime


class DifficultyMix(BaseModel):
    beginner: int = 0
    intermediate: int = 0
    advanced: int = 0

    @field_validator("beginner", "intermediate", "advanced")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Count cannot be negative")
        return v


class AssessmentConfigCreate(BaseModel):
    title: str
    technology_id: str
    difficulty_mix: DifficultyMix
    total_questions: int
    duration_minutes: int = 60
    passing_score: int = 60
    instructions: Optional[str] = None
    original_command: Optional[str] = None

    @field_validator("total_questions")
    @classmethod
    def validate_total(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Must have at least 1 question")
        return v

    @field_validator("passing_score")
    @classmethod
    def validate_passing(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("Passing score must be 0-100")
        return v


class AssessmentConfigUpdate(BaseModel):
    title: Optional[str] = None
    difficulty_mix: Optional[DifficultyMix] = None
    total_questions: Optional[int] = None
    duration_minutes: Optional[int] = None
    passing_score: Optional[int] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None


class AssessmentConfigOut(BaseModel):
    id: str
    access_code: Optional[str] = None
    title: str
    technology_id: str
    technology_name: Optional[str] = None
    technology_icon: Optional[str] = None
    difficulty_mix: dict
    total_questions: int
    duration_minutes: int
    passing_score: int
    instructions: Optional[str] = None
    original_command: Optional[str] = None
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    session_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class GenerateSessionRequest(BaseModel):
    config_id: str
    count: int = 1  # number of access codes to generate


class SessionStart(BaseModel):
    candidate_name: str
    candidate_email: str


class AnswerSubmit(BaseModel):
    question_id: str
    answer_text: Optional[str] = None
    selected_option: Optional[int] = None
    time_spent_seconds: Optional[int] = None


class SessionOut(BaseModel):
    id: str
    config_id: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    # Populated after start
    assessment_title: Optional[str] = None
    technology_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_questions: Optional[int] = None
    # For recruiter results view
    score: Optional[float] = None
    percentage: Optional[float] = None

    model_config = {"from_attributes": True}


class SessionWithQuestions(BaseModel):
    session: SessionOut
    questions: List[dict]  # sanitized questions (no correct_answer for MCQ)


class AgentCommandRequest(BaseModel):
    command: str


class AgentCommandResponse(BaseModel):
    success: bool
    parsed_config: Optional[dict] = None
    message: str
    raw_response: Optional[str] = None
