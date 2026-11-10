from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PerQuestionScore(BaseModel):
    question_id: str
    question_text: str
    question_type: str
    candidate_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    score: float
    max_score: float
    is_correct: Optional[bool] = None
    ai_feedback: Optional[str] = None


class ResultOut(BaseModel):
    id: str
    session_id: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    assessment_title: Optional[str] = None
    technology_name: Optional[str] = None
    total_score: float
    max_possible_score: float
    percentage: float
    passed: bool
    per_question_scores: Optional[list] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    ai_feedback: Optional[str] = None
    shortlisted: Optional[bool] = None
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class ShortlistRequest(BaseModel):
    config_id: str
    min_percentage: float  # minimum % to be shortlisted
    max_percentage: Optional[float] = None  # optional upper bound


class ShortlistResponse(BaseModel):
    shortlisted: List[ResultOut]
    rejected: List[ResultOut]
    total_candidates: int
    shortlisted_count: int
    min_percentage: float
