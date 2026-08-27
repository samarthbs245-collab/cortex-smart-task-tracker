import csv
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.task import Task


# ============================================================
# ALLOWED VALUES
# ============================================================

ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "urgent",
}

# IMPORTANT:
# These values match the main CORTEX task system.
ALLOWED_STATUSES = {
    "todo",
    "in_progress",
    "done",
}


# ============================================================
# BASIC CLEANING
# ============================================================

def _clean(value):
    """
    Remove leading/trailing whitespace.

    Empty values become None.
    """

    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


# ============================================================
# PRIORITY NORMALIZATION
# ============================================================

def _normalize_priority(value):
    """
    Convert messy CSV priority values into
    CORTEX's canonical priority values.
    """

    value = (_clean(value) or "medium").lower()

    aliases = {
        "normal": "medium",
        "med": "medium",
        "medium priority": "medium",

        "high priority": "high",

        "low priority": "low",

        "critical": "urgent",
        "critical/high": "urgent",
    }

    value = aliases.get(
        value,
        value,
    )

    if value not in ALLOWED_PRIORITIES:
        # Safe fallback for unknown/messy values.
        return "medium"

    return value


# ============================================================
# STATUS NORMALIZATION
# ============================================================

def _normalize_status(value):
    """
    Convert messy CSV status values into
    CORTEX's canonical status values.
    """

    value = (_clean(value) or "todo").lower()

    aliases = {
        "to do": "todo",
        "to_do": "todo",
        "not started": "todo",
        "backlog": "todo",
        "todo": "todo",

        "in progress": "in_progress",
        "in-progress": "in_progress",
        "in_progress": "in_progress",
        "inprogress": "in_progress",
        "working": "in_progress",
        "doing": "in_progress",
        "progress": "in_progress",

        "completed": "done",
        "complete": "done",
        "finished": "done",
        "done": "done",
    }

    value = aliases.get(
        value,
        value,
    )

    if value not in ALLOWED_STATUSES:
        # Safe fallback for unknown/messy values.
        return "todo"

    return value


# ============================================================
# DATE PARSER
# ============================================================

def _parse_due_date(value):
    """
    Try several common date formats.

    Invalid or missing dates do not break the import.
    They become None.
    """

    value = _clean(value)

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",

        "%d-%m-%Y",
        "%d/%m/%Y",

        "%m/%d/%Y",

        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt,
            )
        except ValueError:
            continue

    return None


# ============================================================
# CSV IMPORT
# ============================================================

def import_tasks_from_csv(
    file,
    db: Session,
    user_id: int,
):
    """
    Import tasks from one CSV file.

    Expected columns:

        title
        description
        priority
        status
        due_date

    Messy values are cleaned and normalized.

    Rows without a usable title are skipped.

    Invalid priority/status values receive safe defaults
    instead of crashing the entire import.
    """

    # --------------------------------------------------------
    # GET RAW FILE
    # --------------------------------------------------------

    if hasattr(file, "file"):
        raw_file = file.file
    else:
        raw_file = file

    # --------------------------------------------------------
    # READ CONTENT
    # --------------------------------------------------------

    if hasattr(raw_file, "read"):
        content = raw_file.read()
    else:
        content = raw_file

    # --------------------------------------------------------
    # HANDLE BYTES
    # --------------------------------------------------------

    if isinstance(content, bytes):
        content = content.decode(
            "utf-8-sig",
            errors="replace",
        )

    # --------------------------------------------------------
    # EMPTY FILE
    # --------------------------------------------------------

    if not content or not str(content).strip():

        return {
            "imported_count": 0,
            "skipped_count": 0,
            "cleaned_count": 0,
            "imported": [],
            "skipped": [],
            "cleaned": [],
        }

    # --------------------------------------------------------
    # CSV READER
    # --------------------------------------------------------

    reader = csv.DictReader(
        str(content).splitlines()
    )

    # Check whether the CSV actually has headers.
    if not reader.fieldnames:

        return {
            "imported_count": 0,
            "skipped_count": 1,
            "cleaned_count": 0,
            "imported": [],
            "skipped": [
                {
                    "row": 1,
                    "reason": "CSV file has no header row.",
                }
            ],
            "cleaned": [],
        }

    # Normalize header names.
    normalized_headers = {}

    for header in reader.fieldnames:

        if header is None:
            continue

        clean_header = (
            str(header)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        normalized_headers[header] = clean_header

    imported = []
    skipped = []
    cleaned = []

    # --------------------------------------------------------
    # PROCESS ROWS
    # --------------------------------------------------------

    for row_number, raw_row in enumerate(
        reader,
        start=2,
    ):

        try:

            # ------------------------------------------------
            # NORMALIZE COLUMN NAMES
            # ------------------------------------------------

            row = {}

            for original_key, value in raw_row.items():

                if original_key is None:
                    continue

                normalized_key = (
                    normalized_headers
                    .get(original_key)
                )

                if normalized_key:
                    row[normalized_key] = value

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

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

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            description = _clean(
                row.get("description")
            )

            # ------------------------------------------------
            # PRIORITY
            # ------------------------------------------------

            original_priority = _clean(
                row.get("priority")
            )

            priority = _normalize_priority(
                original_priority
            )

            if (
                original_priority is None
                or original_priority.lower()
                != priority.lower()
            ):

                cleaned.append(
                    {
                        "row": row_number,
                        "field": "priority",
                        "from": original_priority,
                        "to": priority,
                    }
                )

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            original_status = _clean(
                row.get("status")
            )

            status = _normalize_status(
                original_status
            )

            if (
                original_status is None
                or original_status.lower()
                != status.lower()
            ):

                cleaned.append(
                    {
                        "row": row_number,
                        "field": "status",
                        "from": original_status,
                        "to": status,
                    }
                )

            # ------------------------------------------------
            # DUE DATE
            # ------------------------------------------------

            original_due_date = _clean(
                row.get("due_date")
            )

            due_date = _parse_due_date(
                original_due_date
            )

            # If a value was supplied but couldn't be parsed,
            # record it as a cleanup rather than failing.
            if (
                original_due_date
                and due_date is None
            ):

                cleaned.append(
                    {
                        "row": row_number,
                        "field": "due_date",
                        "from": original_due_date,
                        "to": None,
                    }
                )

            # ------------------------------------------------
            # CREATE TASK
            # ------------------------------------------------

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

    # --------------------------------------------------------
    # SAVE IMPORTED TASKS
    # --------------------------------------------------------

    db.commit()

    return {
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "cleaned_count": len(cleaned),
        "imported": imported,
        "skipped": skipped,
        "cleaned": cleaned,
    }