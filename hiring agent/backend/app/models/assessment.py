import uuid
from datetime import datetime
from sqlalchemy import (
    String, Boolean, DateTime, Text, Integer, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AssessmentConfig(Base):
    """Recruiter-defined assessment blueprint."""
    __tablename__ = "assessment_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Unique 8-char alphanumeric code shared with candidates
    access_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    technology_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("technologies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # {"beginner": 0, "intermediate": 20, "advanced": 10}
    difficulty_mix: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    passing_score: Mapped[int] = mapped_column(Integer, default=0)  # percentage
    instructions: Mapped[str] = mapped_column(Text, nullable=True)
    # AI-generated command that produced this config
    original_command: Mapped[str] = mapped_column(Text, nullable=True)
    # Snapshot of selected question IDs
    question_ids: Mapped[list] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    technology: Mapped["Technology"] = relationship("Technology", back_populates="assessment_configs")
    sessions: Mapped[list["AssessmentSession"]] = relationship(
        "AssessmentSession", back_populates="config", lazy="select", cascade="all, delete-orphan", uselist=True
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<AssessmentConfig '{self.title}'>"


class AssessmentSession(Base):
    """A unique candidate session linked to an assessment config via access code."""
    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_configs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_name: Mapped[str] = mapped_column(String(200), nullable=True)
    candidate_email: Mapped[str] = mapped_column(String(255), nullable=True)
    # Ordered list of question IDs for this session
    question_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "in_progress", "submitted", "evaluated", name="session_status"),
        default="pending",
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    config: Mapped["AssessmentConfig"] = relationship("AssessmentConfig", back_populates="sessions")
    answers: Mapped[list["CandidateAnswer"]] = relationship(
        "CandidateAnswer", back_populates="session", lazy="select", cascade="all, delete-orphan", uselist=True
    )
    result: Mapped["AssessmentResult"] = relationship(
        "AssessmentResult", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Session {self.id} [{self.status}]>"


class CandidateAnswer(Base):
    """Individual answer submitted by a candidate."""
    __tablename__ = "candidate_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=True)
    selected_option: Mapped[int] = mapped_column(Integer, nullable=True)  # 0-indexed for MCQ
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["AssessmentSession"] = relationship("AssessmentSession", back_populates="answers")
    question: Mapped["Question"] = relationship("Question")

    def __repr__(self):
        return f"<Answer session={self.session_id[:8]} q={self.question_id[:8]}>"
