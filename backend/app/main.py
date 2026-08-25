from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# Import models
from app.models.user import User
from app.models.task import Task

# Import routers
from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# CREATE FASTAPI APP
# ============================================================

app = FastAPI(
    title="CORTEX API",
    version="1.0.0",
    description="AI-powered Smart Task Tracker API",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    # Allow local frontend
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
# AUTHENTICATION ROUTER
# ============================================================

app.include_router(
    auth_router,
)


# ============================================================
# TASK ROUTER
# ============================================================

app.include_router(
    tasks_router,
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to CORTEX API",
        "status": "running",
        "version": "1.0.0",
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