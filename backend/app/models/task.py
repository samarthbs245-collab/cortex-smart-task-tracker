from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="todo",
        nullable=False,
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # AI-generated priority suggestion
    ai_priority: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # AI explanation for the suggested priority
    ai_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Used for reminder tracking
    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # User relationship
    user = relationship(
        "User",
        back_populates="tasks",
    )

    # Subtask relationship
    subtasks = relationship(
        "Subtask",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="Subtask.position",
    )