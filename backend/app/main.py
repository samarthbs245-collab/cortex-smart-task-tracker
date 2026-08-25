from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# ============================================================
# MODELS
# ============================================================

from app.models.user import User
from app.models.task import Task
from app.models.subtask import Subtask
from app.models.notification import Notification

# ============================================================
# ROUTERS
# ============================================================

from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router
from app.routers.ai import router as ai_router


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="CORTEX API",
    version="2.0.0",
    description=(
        "CORTEX — AI-powered Smart Task Tracker "
        "with multi-user authentication, "
        "task intelligence, analytics, and AI assistance."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth_router,
)

app.include_router(
    tasks_router,
)

app.include_router(
    ai_router,
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to CORTEX API",
        "status": "running",
        "version": "2.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CORTEX API",
    }


# ============================================================
# API INFORMATION
# ============================================================

@app.get("/api")
def api_info():
    return {
        "name": "CORTEX API",
        "version": "2.0.0",
        "features": [
            "authentication",
            "profile",
            "tasks",
            "subtasks",
            "search",
            "filters",
            "statistics",
            "reminders",
            "ai-assistant",
        ],
    }