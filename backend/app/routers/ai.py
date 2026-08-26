from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import Task
from app.models.user import User
from app.security import limiter
from app.services.ai_service import ai
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/api/ai",
    tags=["CORTEX AI"],
)


# ============================================================
# ANALYZE TASK
# ============================================================

@router.post("/analyze-task")
@limiter.limit("20/minute")
def analyze_task(
    request: Request,
    payload: dict,
    current_user: User = Depends(
        get_current_user
    ),
):
    title = str(
        payload.get("title", "")
    ).strip()

    description = payload.get(
        "description"
    )

    if not title:
        return {
            "priority": "medium",
            "reason": "A task title is required.",
            "subtasks": [],
        }

    return ai.analyze_task(
        title,
        description,
    )


# ============================================================
# AI ASSISTANT
# ============================================================

@router.post("/assistant")
@limiter.limit("20/minute")
def assistant(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    message = str(
        payload.get(
            "message",
            "",
        )
    ).strip()

    if not message:
        return {
            "answer": (
                "Tell me what you need help with."
            )
        }

    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id
        )
        .order_by(
            Task.created_at.desc()
        )
        .limit(50)
        .all()
    )

    task_context = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "due_date": (
                task.due_date.isoformat()
                if task.due_date
                else None
            ),
        }
        for task in tasks
    ]

    return {
        "answer": ai.assistant(
            message,
            task_context,
        )
    }