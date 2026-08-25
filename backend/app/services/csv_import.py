import csv
from datetime import datetime
from io import TextIOWrapper

from sqlalchemy.orm import Session

from app.models.task import Task


ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "urgent",
}

ALLOWED_STATUSES = {
    "todo",
    "in-progress",
    "done",
}


def _clean(value):
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _normalize_priority(value):
    value = (_clean(value) or "medium").lower()

    # Handle common messy CSV values.
    aliases = {
        "normal": "medium",
        "med": "medium",
        "high priority": "high",
        "low priority": "low",
        "critical": "urgent",
        "critical/high": "urgent",
    }

    value = aliases.get(value, value)

    if value not in ALLOWED_PRIORITIES:
        return "medium"

    return value


def _normalize_status(value):
    value = (_clean(value) or "todo").lower()

    aliases = {
        "to do": "todo",
        "not started": "todo",
        "in progress": "in-progress",
        "in_progress": "in-progress",
        "working": "in-progress",
        "completed": "done",
        "complete": "done",
        "finished": "done",
    }

    value = aliases.get(value, value)

    if value not in ALLOWED_STATUSES:
        return "todo"

    return value


def _parse_due_date(value):
    value = _clean(value)

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def import_tasks_from_csv(
    file,
    db: Session,
    user_id: int,
):
    """
    Import tasks from a CSV file.

    Expected columns:
    title
    description
    priority
    status
    due_date

    Messy values are normalized instead of crashing
    the whole import.
    """

    if hasattr(file, "file"):
        raw_file = file.file
    else:
        raw_file = file

    if hasattr(raw_file, "read"):
        content = raw_file.read()

    else:
        content = raw_file

    if isinstance(content, bytes):
        content = content.decode(
            "utf-8-sig",
            errors="replace",
        )

    reader = csv.DictReader(
        content.splitlines()
    )

    imported = []
    skipped = []

    for row_number, row in enumerate(
        reader,
        start=2,
    ):
        try:
            title = _clean(
                row.get("title")
            )

            if not title:
                skipped.append(
                    {
                        "row": row_number,
                        "reason": "Missing title.",
                    }
                )
                continue

            description = _clean(
                row.get("description")
            )

            priority = _normalize_priority(
                row.get("priority")
            )

            status = _normalize_status(
                row.get("status")
            )

            due_date = _parse_due_date(
                row.get("due_date")
            )

            task = Task(
                user_id=user_id,
                title=title[:255],
                description=description,
                priority=priority,
                status=status,
                due_date=due_date,
            )

            db.add(task)

            imported.append(
                {
                    "row": row_number,
                    "title": title,
                }
            )

        except Exception as exc:
            skipped.append(
                {
                    "row": row_number,
                    "reason": str(exc),
                }
            )

    db.commit()

    return {
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped,
    }