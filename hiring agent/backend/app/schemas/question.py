from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class MCQOption(BaseModel):
    label: str  # A, B, C, D
    text: str
    is_correct: bool = False


class QuestionCreate(BaseModel):
    technology_id: str
    question_type: Literal["mcq", "true_false", "short_answer", "code"] = "mcq"
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    question_text: str
    options: Optional[List[MCQOption]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    max_score: int = 10
    tags: Optional[List[str]] = None
    source: str = "manual"


class QuestionUpdate(BaseModel):
    question_type: Optional[Literal["mcq", "true_false", "short_answer", "code"]] = None
    difficulty: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    question_text: Optional[str] = None
    options: Optional[List[MCQOption]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    max_score: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TechnologyOut(BaseModel):
    id: str
    name: str
    slug: str
    icon: Optional[str] = None
    color: Optional[str] = None

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: str
    technology_id: str
    technology: Optional[TechnologyOut] = None
    question_type: str
    difficulty: str
    question_text: str
    options: Optional[list] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    max_score: int
    tags: Optional[List[str]] = None
    is_active: bool
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionFilter(BaseModel):
    technology_id: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    search: Optional[str] = None
    is_active: Optional[bool] = True
    page: int = 1
    page_size: int = 20


class PaginatedQuestions(BaseModel):
    items: List[QuestionOut]
    total: int
    page: int
    page_size: int
    total_pages: int
