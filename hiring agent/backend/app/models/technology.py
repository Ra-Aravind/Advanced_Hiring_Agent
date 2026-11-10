import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Technology(Base):
    __tablename__ = "technologies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(10), nullable=True)  # emoji
    color: Mapped[str] = mapped_column(String(20), nullable=True)  # hex color
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    questions: Mapped[list] = relationship("Question", back_populates="technology", lazy="select")
    assessment_configs: Mapped[list] = relationship(
        "AssessmentConfig", back_populates="technology", lazy="select"
    )

    def __repr__(self):
        return f"<Technology {self.name}>"
