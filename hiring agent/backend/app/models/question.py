import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    technology_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("technologies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_type: Mapped[str] = mapped_column(
        SAEnum("mcq", "true_false", "short_answer", "code", name="question_type"),
        nullable=False,
        default="mcq",
    )
    difficulty: Mapped[str] = mapped_column(
        SAEnum("beginner", "intermediate", "advanced", name="difficulty_level"),
        nullable=False,
        default="intermediate",
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    # For MCQ: [{"label": "A", "text": "...", "is_correct": true/false}]
    options: Mapped[dict] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    max_score: Mapped[int] = mapped_column(Integer, default=10)
    tags: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Source: 'ai_generated' or 'manual'
    source: Mapped[str] = mapped_column(String(20), default="ai_generated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    technology: Mapped["Technology"] = relationship("Technology", back_populates="questions")

    def __repr__(self):
        return f"<Question {self.id[:8]} [{self.difficulty}] {self.question_type}>"
