from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# SUBTASK
# ============================================================

class SubtaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )


class SubtaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    position: int

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# TASK CREATE
# ============================================================

class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high|urgent)$",
    )

    status: str = Field(
        default="todo",
        pattern="^(todo|in_progress|done)$",
    )

    due_date: datetime | None = None

    subtasks: list[SubtaskCreate] = Field(
        default_factory=list,
    )


# ============================================================
# TASK UPDATE
# ============================================================

class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    priority: str | None = Field(
        default=None,
        pattern="^(low|medium|high|urgent)$",
    )

    status: str | None = Field(
        default=None,
        pattern="^(todo|in_progress|done)$",
    )

    due_date: datetime | None = None


# ============================================================
# TASK RESPONSE
# ============================================================

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None

    priority: str
    status: str

    due_date: datetime | None

    user_id: int

    ai_priority: str | None
    ai_reason: str | None

    subtasks: list[SubtaskResponse] = Field(
        default_factory=list,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

class StatsResponse(BaseModel):
    total: int
    completed: int
    in_progress: int
    todo: int
    overdue: int
    due_today: int
    urgent: int
    completion_rate: float