from sqlalchemy import (
    Column,
    String,
    Numeric,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from app.database import Base


class InterviewFeedback(Base):

    __tablename__ = "interview_feedback"

    feedback_id = Column(
        String(50),
        primary_key=True
    )

    interview_id = Column(
        String(50),
        ForeignKey("interviews.interview_id"),
        nullable=False
    )

    interviewer_id = Column(
        String(50),
        ForeignKey("interviewers.interviewer_id"),
        nullable=False
    )

    technical_score = Column(
        Numeric(4, 2)
    )

    problem_solving_score = Column(
        Numeric(4, 2)
    )

    communication_score = Column(
        Numeric(4, 2)
    )

    coding_score = Column(
        Numeric(4, 2)
    )

    confidence_score = Column(
        Numeric(4, 2)
    )

    overall_score = Column(
        Numeric(4, 2)
    )

    strengths = Column(String)

    weaknesses = Column(String)

    technical_comments = Column(String)

    recommendation = Column(
        String(30)
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )