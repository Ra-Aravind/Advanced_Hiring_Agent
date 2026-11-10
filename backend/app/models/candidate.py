from sqlalchemy import (
    Column,
    String,
    Boolean,
    Numeric,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from app.database import Base


class Candidate(Base):

    __tablename__ = "candidates"

    candidate_id = Column(
        String(50),
        primary_key=True
    )

    user_id = Column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False,
        unique=True
    )

    resume_url = Column(String)

    experience_years = Column(
        Numeric(4, 1)
    )

    primary_skill = Column(
        String(100)
    )

    phase1_assessment_id = Column(
        String(50)
    )

    phase1_score = Column(
        Numeric(5, 2)
    )

    phase1_status = Column(
        String(30)
    )

    interview_eligible = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )