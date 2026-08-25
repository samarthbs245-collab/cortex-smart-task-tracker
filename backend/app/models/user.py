from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    # ============================================================
    # USER ID
    # ============================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ============================================================
    # BASIC INFORMATION
    # ============================================================

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ============================================================
    # PERSONALIZATION INFORMATION
    # ============================================================

    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    goal: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    available_hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ============================================================
    # ACCOUNT CREATION TIME
    # ============================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ============================================================
    # TASK RELATIONSHIP
    # ============================================================

    tasks = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
    )