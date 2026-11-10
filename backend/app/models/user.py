from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class User(Base):

    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)

    name = Column(String(150), nullable=False)

    email = Column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash = Column(String(255))

    role = Column(String(30), nullable=False)

    phone = Column(String(30))

    status = Column(
        String(20),
        default="ACTIVE"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )