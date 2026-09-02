from datetime import date, datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy import or_, case
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.subtask import Subtask
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    StatsResponse,
    SubtaskCreate,
    SubtaskResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.auth_dependency import get_current_user
from app.services.csv_import import import_tasks_from_csv


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
)


# ============================================================
# CONSTANTS
# ============================================================

VALID_STATUSES = {
    "todo",
    "in_progress",
    "done",
}

VALID_PRIORITIES = {
    "low",
    "medium",
    "high",
    "urgent",
}


# ============================================================
# STATUS NORMALIZER
# ============================================================

def normalize_status(value: str) -> str:
    """
    Keep one canonical representation everywhere:
        todo
        in_progress
        done
    """

    value = (
        str(value)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    aliases = {
        "to_do": "todo",
        "todo": "todo",
        "in_progress": "in_progress",
        "inprogress": "in_progress",
        "progress": "in_progress",
        "done": "done",
        "completed": "done",
        "complete": "done",
    }

    normalized = aliases.get(
        value,
        value,
    )

    if normalized not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Status must be todo, "
                "in_progress, or done."
            ),
        )

    return normalized


# ============================================================
# PRIORITY NORMALIZER
# ============================================================

def normalize_priority(value: str) -> str:
    value = (
        str(value)
        .strip()
        .lower()
    )

    if value not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Priority must be low, medium, "
                "high, or urgent."
            ),
        )

    return value


# ============================================================
# HELPER — GET USER'S OWN TASK
# ============================================================

def _get_owned_task(
    task_id: int,
    db: Session,
    user_id: int,
) -> Task:

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.user_id == user_id,
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    return task


# ============================================================
# CREATE TASK
# ============================================================

@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    title = data.title.strip()

    if not title:
        raise HTTPException(
            status_code=422,
            detail="Task title is required.",
        )

    priority = normalize_priority(
        data.priority
    )

    status_value = normalize_status(
        data.status
    )

    task = Task(
        title=title,
        description=(
            data.description.strip()
            if data.description
            else None
        ),
        priority=priority,
        status=status_value,
        due_date=data.due_date,
        user_id=current_user.id,
    )

    db.add(task)
    db.flush()

    # --------------------------------------------------------
    # CREATE SUBTASKS
    # --------------------------------------------------------

    for index, subtask_data in enumerate(
        data.subtasks
    ):

        subtask_title = (
            subtask_data.title.strip()
        )

        if subtask_title:

            db.add(
                Subtask(
                    task_id=task.id,
                    title=subtask_title,
                    position=index,
                )
            )

    db.commit()
    db.refresh(task)

    return task


# ============================================================
# GET TASKS
# ============================================================

@router.get(
    "",
    response_model=list[TaskResponse],
)
def get_tasks(
    search: str | None = None,

    status_filter: str = Query(
        "all",
        alias="status",
    ),

    priority: str = "all",

    due: str = "all",

    sort: str = "newest",

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    query = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id
        )
    )

    # ========================================================
    # SEARCH
    # ========================================================

    if search and search.strip():

        search_text = (
            f"%{search.strip()}%"
        )

        query = query.filter(
            or_(
                Task.title.ilike(
                    search_text
                ),
                Task.description.ilike(
                    search_text
                ),
            )
        )

    # ========================================================
    # STATUS FILTER
    # ========================================================

    if status_filter != "all":

        normalized_status = (
            normalize_status(
                status_filter
            )
        )

        query = query.filter(
            Task.status == normalized_status
        )

    # ========================================================
    # PRIORITY FILTER
    # ========================================================

    if priority != "all":

        normalized_priority = (
            normalize_priority(
                priority
            )
        )

        query = query.filter(
            Task.priority == normalized_priority
        )

    # ========================================================
    # DUE DATE FILTER
    # ========================================================

    now = datetime.now()

    today = date.today()

    start_of_today = datetime.combine(
        today,
        datetime.min.time(),
    )

    start_of_tomorrow = (
        start_of_today
        + timedelta(days=1)
    )

    if due == "overdue":

        query = query.filter(
            Task.due_date < now,
            Task.status != "done",
        )

    elif due == "today":

        query = query.filter(
            Task.due_date >= start_of_today,
            Task.due_date < start_of_tomorrow,
            Task.status != "done",
        )

    elif due == "upcoming":

        query = query.filter(
            Task.due_date >= now,
            Task.status != "done",
        )

    # ========================================================
    # SORTING
    # ========================================================

    if sort == "due":

        query = query.order_by(
            Task.due_date.asc().nullslast(),
            Task.created_at.desc(),
        )

    elif sort == "priority":

        priority_order = case(
            {
                "urgent": 4,
                "high": 3,
                "medium": 2,
                "low": 1,
            },
            value=Task.priority,
            else_=0,
        )

        query = query.order_by(
            priority_order.desc(),
            Task.created_at.desc(),
        )

    elif sort == "oldest":

        query = query.order_by(
            Task.created_at.asc()
        )

    else:

        query = query.order_by(
            Task.created_at.desc()
        )

    return query.all()


# ============================================================
# BULK CSV IMPORT
# ============================================================

@router.post("/import-csv")
def import_csv_files(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import tasks from one or more CSV files.

    Each CSV is processed independently.
    Messy rows are cleaned or skipped by the CSV import service.
    """

    total_imported = 0
    total_skipped = 0
    total_cleaned = 0

    file_results = []

    for file in files:

        # Only accept CSV files.
        if not file.filename.lower().endswith(".csv"):
            file_results.append(
                {
                    "filename": file.filename,
                    "imported_count": 0,
                    "skipped_count": 0,
                    "cleaned_count": 0,
                    "error": "Only CSV files are allowed.",
                }
            )
            continue

        try:
            result = import_tasks_from_csv(
                file=file,
                db=db,
                user_id=current_user.id,
            )

            total_imported += result["imported_count"]
            total_skipped += result["skipped_count"]
            total_cleaned += result["cleaned_count"]

            file_results.append(
                {
                    "filename": file.filename,
                    **result,
                }
            )

        except Exception as exc:
            db.rollback()

            file_results.append(
                {
                    "filename": file.filename,
                    "imported_count": 0,
                    "skipped_count": 0,
                    "cleaned_count": 0,
                    "error": str(exc),
                }
            )

    return {
        "message": "CSV import completed.",
        "total_files": len(files),
        "total_imported": total_imported,
        "total_skipped": total_skipped,
        "total_cleaned": total_cleaned,
        "files": file_results,
    }

# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@router.get(
    "/stats",
    response_model=StatsResponse,
)
def get_stats(
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
        .all()
    )

    total = len(tasks)

    today = date.today()

    start_of_today = datetime.combine(
        today,
        datetime.min.time(),
    )

    start_of_tomorrow = (
        start_of_today
        + timedelta(days=1)
    )

    now = datetime.now()

    completed = sum(
        task.status == "done"
        for task in tasks
    )

    in_progress = sum(
        task.status == "in_progress"
        for task in tasks
    )

    todo = sum(
        task.status == "todo"
        for task in tasks
    )

    overdue = sum(
        bool(
            task.due_date
            and task.due_date < now
            and task.status != "done"
        )
        for task in tasks
    )

    due_today = sum(
        bool(
            task.due_date
            and start_of_today
            <= task.due_date
            < start_of_tomorrow
            and task.status != "done"
        )
        for task in tasks
    )

    urgent = sum(
        task.priority == "urgent"
        and task.status != "done"
        for task in tasks
    )

    completion_rate = (
        round(
            (completed / total) * 100,
            1,
        )
        if total
        else 0
    )

    return StatsResponse(
        total=total,
        completed=completed,
        in_progress=in_progress,
        todo=todo,
        overdue=overdue,
        due_today=due_today,
        urgent=urgent,
        completion_rate=completion_rate,
    )


# ============================================================
# DUE-DATE REMINDERS
# ============================================================

@router.get(
    "/reminders",
)
def get_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    now = datetime.now()

    next_24_hours = (
        now + timedelta(hours=24)
    )

    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id,
            Task.status != "done",
            Task.due_date.isnot(None),
            Task.due_date <= next_24_hours,
        )
        .order_by(
            Task.due_date.asc()
        )
        .all()
    )

    reminders = []

    for task in tasks:

        reminder_type = (
            "overdue"
            if task.due_date < now
            else "due_soon"
        )

        reminders.append(
            {
                "task_id": task.id,
                "title": task.title,
                "due_date": task.due_date,
                "type": reminder_type,
                "priority": task.priority,
            }
        )

    return reminders


# ============================================================
# ✅ COMPLETE TASK
# ============================================================

@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
)
def complete_task(
    task_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    task = _get_owned_task(
        task_id,
        db,
        current_user.id,
    )

    task.status = "done"

    db.commit()
    db.refresh(task)

    return task


# ============================================================
# GET SINGLE TASK
# ============================================================

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    return _get_owned_task(
        task_id,
        db,
        current_user.id,
    )


# ============================================================
# UPDATE TASK
# ============================================================

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,

    data: TaskUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    task = _get_owned_task(
        task_id,
        db,
        current_user.id,
    )

    update_data = data.model_dump(
        exclude_unset=True
    )

    # ========================================================
    # VALIDATE + NORMALIZE
    # ========================================================

    if "title" in update_data:

        if update_data["title"] is None:

            raise HTTPException(
                status_code=422,
                detail="Task title cannot be empty.",
            )

        update_data["title"] = (
            update_data["title"]
            .strip()
        )

        if not update_data["title"]:

            raise HTTPException(
                status_code=422,
                detail="Task title cannot be empty.",
            )

    if "description" in update_data:

        if update_data["description"]:

            update_data["description"] = (
                update_data["description"]
                .strip()
            )

    if "status" in update_data:

        update_data["status"] = (
            normalize_status(
                update_data["status"]
            )
        )

    if "priority" in update_data:

        update_data["priority"] = (
            normalize_priority(
                update_data["priority"]
            )
        )

    # ========================================================
    # UPDATE
    # ========================================================

    for field, value in update_data.items():

        setattr(
            task,
            field,
            value,
        )

    db.commit()
    db.refresh(task)

    return task

# ============================================================
# CLEAR ALL TASKS
# ============================================================

@router.delete("/clear-all")
def clear_all_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    task_ids = [
        task.id
        for task in (
            db.query(Task.id)
            .filter(
                Task.user_id == current_user.id
            )
            .all()
        )
    ]

    if not task_ids:
        return {
            "message": "No tasks to clear.",
            "deleted_count": 0,
        }

    # Delete subtasks first
    db.query(Subtask).filter(
        Subtask.task_id.in_(task_ids)
    ).delete(
        synchronize_session=False
    )

    # Delete all tasks belonging to the current user
    deleted_count = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id
        )
        .delete(
            synchronize_session=False
        )
    )

    db.commit()

    return {
        "message": "All tasks cleared successfully.",
        "deleted_count": deleted_count,
    }


# ============================================================
# DELETE TASK
# ============================================================

@router.delete(
    "/{task_id}",
)
def delete_task(
    task_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):
    task = _get_owned_task(
        task_id,
        db,
        current_user.id,
    )

    db.delete(task)
    db.commit()

    return {
        "message": "Task deleted successfully."
    }

# ============================================================
# ADD SUBTASK
# ============================================================

@router.post(
    "/{task_id}/subtasks",
    response_model=SubtaskResponse,
    status_code=201,
)
def add_subtask(
    task_id: int,

    data: SubtaskCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    task = _get_owned_task(
        task_id,
        db,
        current_user.id,
    )

    position = len(
        task.subtasks
    )

    title = data.title.strip()

    if not title:

        raise HTTPException(
            status_code=422,
            detail="Subtask title is required.",
        )

    subtask = Subtask(
        task_id=task.id,
        title=title,
        position=position,
    )

    db.add(subtask)
    db.commit()
    db.refresh(subtask)

    return subtask


# ============================================================
# UPDATE SUBTASK
# ============================================================

@router.patch(
    "/subtasks/{subtask_id}",
)
def update_subtask(
    subtask_id: int,

    completed: bool | None = None,

    title: str | None = None,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    subtask = (
        db.query(Subtask)
        .join(Task)
        .filter(
            Subtask.id == subtask_id,
            Task.user_id == current_user.id,
        )
        .first()
    )

    if not subtask:

        raise HTTPException(
            status_code=404,
            detail="Subtask not found.",
        )

    if completed is not None:

        subtask.completed = completed

    if title is not None:

        cleaned_title = title.strip()

        if not cleaned_title:

            raise HTTPException(
                status_code=422,
                detail="Subtask title cannot be empty.",
            )

        subtask.title = cleaned_title

    db.commit()
    db.refresh(subtask)

    return {
        "id": subtask.id,
        "title": subtask.title,
        "completed": subtask.completed,
        "position": subtask.position,
    }


# ============================================================
# DELETE SUBTASK
# ============================================================

@router.delete(
    "/subtasks/{subtask_id}",
)
def delete_subtask(
    subtask_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    subtask = (
        db.query(Subtask)
        .join(Task)
        .filter(
            Subtask.id == subtask_id,
            Task.user_id == current_user.id,
        )
        .first()
    )

    if not subtask:

        raise HTTPException(
            status_code=404,
            detail="Subtask not found.",
        )

    db.delete(subtask)
    db.commit()

    return {
        "message": "Subtask deleted successfully."
    }