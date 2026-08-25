from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import Task
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.ai_service import ai


router = APIRouter(
    prefix="/api/ai",
    tags=["CORTEX AI"],
)


# ============================================================
# ANALYZE TASK
# ============================================================

@router.post("/analyze-task")
def analyze_task(
    payload: dict,
    current_user: User = Depends(
        get_current_user
    ),
):
    return ai.analyze_task(
        payload.get("title", ""),
        payload.get("description"),
    )


# ============================================================
# AI ASSISTANT
# ============================================================

@router.post("/assistant")
def assistant(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
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

    context = [
        {
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "due_date": task.due_date,
        }
        for task in tasks
    ]

    return {
        "answer": ai.assistant(
            payload.get(
                "message",
                "",
            ),
            context,
        )
    }