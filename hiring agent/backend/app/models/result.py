import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AssessmentResult(Base):
    """Evaluated result for a candidate session."""
    __tablename__ = "assessment_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    total_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_possible_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Per-question breakdown: [{question_id, score, max_score, feedback, is_correct}]
    per_question_scores: Mapped[list] = mapped_column(JSON, nullable=True)
    # AI-generated summary
    strengths: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    ai_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    # Recruiter shortlisting
    shortlisted: Mapped[bool] = mapped_column(Boolean, nullable=True)
    shortlisted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    shortlisted_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["AssessmentSession"] = relationship("AssessmentSession", back_populates="result")

    def __repr__(self):
        return f"<Result {self.session_id[:8]} {self.percentage:.1f}% {'PASS' if self.passed else 'FAIL'}>"
