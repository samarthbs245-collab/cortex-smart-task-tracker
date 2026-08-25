from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

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

    theme: Mapped[str] = mapped_column(
        String(20),
        default="dark",
        nullable=False,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    reset_token_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    tasks = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
    )