from sqlalchemy import (
    Column,
    String,
    Numeric,
    ForeignKey,
    DateTime
)

from sqlalchemy.sql import func

from app.database import Base


class Interviewer(Base):

    __tablename__ = "interviewers"

    interviewer_id = Column(
        String(50),
        primary_key=True
    )

    user_id = Column(
        String(50),
        ForeignKey("users.user_id"),
        nullable=False,
        unique=True
    )

    department = Column(String(120))

    experience_years = Column(
        Numeric(4, 1)
    )

    expertise = Column(String)

    availability_status = Column(
        String(20),
        default="AVAILABLE"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )