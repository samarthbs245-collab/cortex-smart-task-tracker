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

    # --------------------------------------------------------
    # CHECK WHETHER TASK CONTEXT IS ACTUALLY NEEDED
    # --------------------------------------------------------

        # --------------------------------------------------------
    # DETECT SIMPLE CONVERSATION
    # --------------------------------------------------------

    message_lower = message.lower().strip()

    simple_phrases = {
        # Greetings
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "heyy",
        "heyyy",

        # Greeting variations
        "hi there",
        "hello there",
        "hey there",
        "hi bro",
        "hey bro",
        "hello bro",
        "hi cortex",
        "hello cortex",
        "hey cortex",

        # Time-based greetings
        "good morning",
        "good afternoon",
        "good evening",
        "good morning cortex",
        "good afternoon cortex",
        "good evening cortex",

        # Casual conversation
        "how are you",
        "how are you?",
        "how are you doing",
        "how are you doing?",
        "how's it going",
        "how's it going?",
        "whats up",
        "what's up",
        "what's up?",
        "what are you doing",

        # Thanks
        "thanks",
        "thanks!",
        "thanks a lot",
        "thank you",
        "thank you!",
        "thank you so much",
    }

    # --------------------------------------------------------
    # RECOGNIZE COMMON GREETING VARIATIONS
    # --------------------------------------------------------

    is_simple = (
        message_lower in simple_phrases
        or message_lower.startswith("hi ")
        or message_lower.startswith("hey ")
        or message_lower.startswith("hello ")
    )

    needs_tasks = not is_simple
    
    # --------------------------------------------------------
    # ONLY QUERY TASKS WHEN NEEDED
    # --------------------------------------------------------

    task_context = []

    if needs_tasks:

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

    # --------------------------------------------------------
    # SEND TO CORTEX AI
    # --------------------------------------------------------

    return {
        "answer": ai.assistant(
            message,
            task_context,
        )
    }