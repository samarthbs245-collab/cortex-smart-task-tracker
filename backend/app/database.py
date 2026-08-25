import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured."
    )


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# BASE MODEL
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# SMALL DATABASE MIGRATION
# ============================================================

def migrate_schema():
    """
    Idempotent migration for existing CORTEX PostgreSQL
    databases.

    This adds new columns required by the upgraded version
    without deleting existing users or tasks.
    """

    if engine.dialect.name != "postgresql":
        return

    statements = [
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS reset_token_hash VARCHAR(128)
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS reset_token_expires_at TIMESTAMP
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS theme VARCHAR(20)
        DEFAULT 'dark'
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)
        """,
        """
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS ai_priority VARCHAR(20)
        """,
        """
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS ai_reason TEXT
        """,
        """
        ALTER TABLE tasks
        ADD COLUMN IF NOT EXISTS reminder_sent_at TIMESTAMP
        """,
    ]

    with engine.begin() as connection:

        for statement in statements:
            connection.execute(
                text(statement)
            )