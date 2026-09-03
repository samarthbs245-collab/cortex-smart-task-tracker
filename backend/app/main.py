from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.database import initialize_database

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
# RATE LIMITER
# ============================================================

from app.security import limiter


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="CORTEX API",
    version="2.0.0",
    description=(
        "CORTEX — AI-powered Smart Task Tracker "
        "with secure authentication, email verification, "
        "intelligent task management, analytics and AI assistance."
    ),
)


# ============================================================
# RATE LIMITING
# ============================================================

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(
    SlowAPIMiddleware,
)



# ============================================================
# SECURITY HEADERS
# ============================================================

@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next,
):
    response = await call_next(request)

    # Prevent MIME sniffing
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    # Prevent clickjacking
    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    # Control referrer information
    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    # Restrict browser capabilities
    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=()"
    )

    # HSTS only when using HTTPS
    if request.url.scheme == "https":
        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )

    return response

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
        "https://cortex-smart-task-tracker.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# GENERAL SERVER ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    print(
        f"CORTEX SERVER ERROR: "
        f"{type(exc).__name__}: {exc}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error."
        },
    )


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth_router
)

app.include_router(
    tasks_router
)

app.include_router(
    ai_router
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
            "secure-authentication",
            "email-verification",
            "profile",
            "password-reset",
            "tasks",
            "subtasks",
            "priority",
            "search",
            "filters",
            "statistics",
            "reminders",
            "ai-assistant",
            "ai-task-analysis",
        ],
    }


# ============================================================
# SECURITY INFORMATION
# ============================================================

@app.get("/security")
def security_info():
    return {
        "password_storage": "Argon2id hashing",
        "transport": "HTTPS/TLS in production",
        "authentication": "JWT",
        "email_verification": "Enabled",
        "password_reset": "Single-use expiring tokens",
        "database_access": "Server-side only",
        "secrets": "Environment variables",
        "rate_limiting": "Enabled",
    }

# ============================================================
# CUSTOM OPENAPI — CSV FILE UPLOAD FOR SWAGGER
# ============================================================

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    try:
        request_body = (
            openapi_schema["paths"]
            ["/api/tasks/import-csv"]
            ["post"]
            ["requestBody"]
            ["content"]
            ["multipart/form-data"]
            ["schema"]
        )

        # Resolve schema reference if FastAPI generated one
        if "$ref" in request_body:
            ref_name = request_body["$ref"].split("/")[-1]

            request_body = (
                openapi_schema["components"]
                ["schemas"]
                [ref_name]
            )

        files_schema = (
            request_body
            .get("properties", {})
            .get("files")
        )

        if files_schema:
            files_schema["type"] = "array"
            files_schema["items"] = {
                "type": "string",
                "format": "binary",
            }

            # Remove newer schema metadata that can
            # make Swagger render a text field.
            files_schema.pop(
                "contentMediaType",
                None,
            )

            files_schema.pop(
                "contentEncoding",
                None,
            )

    except (KeyError, TypeError):
        pass

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi