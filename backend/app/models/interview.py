from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    Time,
    DateTime,
    ForeignKey
)

from sqlalchemy.sql import func

from app.database import Base


class Interview(Base):

    __tablename__ = "interviews"

    interview_id = Column(
        String(50),
        primary_key=True
    )

    candidate_id = Column(
        String(50),
        ForeignKey("candidates.candidate_id"),
        nullable=False
    )

    interviewer_id = Column(
        String(50),
        ForeignKey("interviewers.interviewer_id"),
        nullable=False
    )

    recruiter_id = Column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False
    )

    interview_type = Column(
        String(50),
        default="TECHNICAL"
    )

    scheduled_date = Column(
        Date,
        nullable=False
    )

    scheduled_time = Column(
        Time,
        nullable=False
    )

    duration_minutes = Column(
        Integer,
        default=45
    )

    platform = Column(
        String(50),
        default="GOOGLE_MEET"
    )

    meeting_id = Column(
        String(255)
    )

    meeting_link = Column(
        String
    )

    status = Column(
        String(30),
        default="SCHEDULED"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    started_at = Column(DateTime)

    ended_at = Column(DateTime)