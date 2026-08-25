from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

from app.models.user import User
from app.models.task import Task

from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="CORTEX API",
    version="1.0.0",
    description="AI-powered Smart Task Tracker API",
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication routes
app.include_router(auth_router)


# Task routes
app.include_router(tasks_router)


# ROOT
@app.get("/")
def root():
    return {
        "message": "Welcome to CORTEX API",
        "status": "running",
        "version": "1.0.0",
    }


# HEALTH CHECK
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CORTEX API",
    }