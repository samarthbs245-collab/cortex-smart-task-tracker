from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
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


router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
)


# ============================================================
# HELPER — GET CURRENT USER'S TASK
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
    current_user: User = Depends(get_current_user),
):

    task = Task(
        title=data.title.strip(),
        description=(
            data.description.strip()
            if data.description
            else None
        ),
        priority=data.priority,
        status=data.status,
        due_date=data.due_date,
        user_id=current_user.id,
    )

    db.add(task)
    db.flush()

    for index, subtask_data in enumerate(
        data.subtasks
    ):
        title = subtask_data.title.strip()

        if title:
            db.add(
                Subtask(
                    task_id=task.id,
                    title=title,
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
    current_user: User = Depends(get_current_user),
):

    query = (
        db.query(Task)
        .filter(
            Task.user_id == current_user.id
        )
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if status_filter != "all":

        normalized_status = (
            status_filter
            .lower()
            .strip()
            .replace("_", "-")
        )

        query = query.filter(
            Task.status == normalized_status
        )

    # --------------------------------------------------------
    # PRIORITY FILTER
    # --------------------------------------------------------

    if priority != "all":

        normalized_priority = (
            priority
            .lower()
            .strip()
        )

        query = query.filter(
            Task.priority
            == normalized_priority
        )

    # --------------------------------------------------------
    # DUE DATE FILTER
    # --------------------------------------------------------

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
        )

    elif due == "upcoming":

        query = query.filter(
            Task.due_date >= now,
        )

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    if sort == "due":

        query = query.order_by(
            Task.due_date.asc().nullslast(),
            Task.created_at.desc(),
        )

    elif sort == "priority":

        # Explicit ordering instead of alphabetical sorting.
        from sqlalchemy import case

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
# DASHBOARD STATISTICS
# ============================================================

@router.get(
    "/stats",
    response_model=StatsResponse,
)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        task.status == "in-progress"
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
    current_user: User = Depends(get_current_user),
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
# GET SINGLE TASK
# ============================================================

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
):

    task = _get_owned_task(
        task_id,
        db,
        current_user.id,
    )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():

        if (
            field == "title"
            and value is not None
        ):
            value = value.strip()

        if (
            field == "description"
            and value is not None
        ):
            value = value.strip()

        if (
            field == "status"
            and value is not None
        ):
            value = (
                value
                .lower()
                .strip()
                .replace("_", "-")
            )

        if (
            field == "priority"
            and value is not None
        ):
            value = (
                value
                .lower()
                .strip()
            )

        setattr(
            task,
            field,
            value,
        )

    db.commit()
    db.refresh(task)

    return task


# ============================================================
# DELETE TASK
# ============================================================

@router.delete(
    "/{task_id}",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
):

    task = _get_owned_task(
        task_id,
        db,
        current_user.id,
    )

    position = len(
        task.subtasks
    )

    subtask = Subtask(
        task_id=task.id,
        title=data.title.strip(),
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
    current_user: User = Depends(get_current_user),
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

        if cleaned_title:
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
    current_user: User = Depends(get_current_user),
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