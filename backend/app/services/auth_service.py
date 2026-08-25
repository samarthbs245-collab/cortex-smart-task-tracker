import hashlib
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from dotenv import load_dotenv
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.user import User


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not configured."
    )


ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

RESET_TOKEN_MINUTES = 30


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    return check_password_hash(
        password_hash,
        password,
    )


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    age: int,
    goal: str | None = None,
    available_hours: float | None = None,
) -> User:

    normalized_email = email.strip().lower()

    existing_user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        age=age,
        goal=goal,
        available_hours=available_hours,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:

    normalized_email = email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
        )

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
        )

    return user


# ============================================================
# JWT ACCESS TOKEN
# ============================================================

def create_access_token(
    user_id: int,
) -> str:

    expires = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expires,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ============================================================
# RESET TOKEN HASH
# ============================================================

def _hash_reset_token(
    token: str,
) -> str:

    return hashlib.sha256(
        token.encode()
    ).hexdigest()


# ============================================================
# REQUEST PASSWORD RESET
# ============================================================

def request_password_reset(
    db: Session,
    email: str,
) -> None:

    normalized_email = email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    # Do not reveal whether the email exists.
    if not user:
        return

    raw_token = secrets.token_urlsafe(32)

    user.reset_token_hash = (
        _hash_reset_token(raw_token)
    )

    user.reset_token_expires_at = (
        datetime.utcnow()
        + timedelta(
            minutes=RESET_TOKEN_MINUTES
        )
    )

    db.commit()

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://127.0.0.1:5500",
    ).rstrip("/")

    reset_url = (
        f"{frontend_url}/reset-password.html"
        f"?token={raw_token}"
    )

    smtp_host = os.getenv("SMTP_HOST")

    smtp_port = int(
        os.getenv(
            "SMTP_PORT",
            "587",
        )
    )

    smtp_username = os.getenv(
        "SMTP_USERNAME"
    )

    smtp_password = os.getenv(
        "SMTP_PASSWORD"
    )

    smtp_sender = os.getenv(
        "SMTP_FROM",
        smtp_username or "noreply@cortex.app",
    )

    # Development fallback.
    if not (
        smtp_host
        and smtp_username
        and smtp_password
    ):

        if (
            os.getenv(
                "APP_ENV",
                "development",
            ).lower()
            == "development"
        ):

            print(
                f"[CORTEX DEV] Password reset URL "
                f"for {user.email}: {reset_url}"
            )

            return

        raise HTTPException(
            status_code=503,
            detail=(
                "Password reset email service "
                "is not configured."
            ),
        )

    # ========================================================
    # SEND RESET EMAIL
    # ========================================================

    message = EmailMessage()

    message["Subject"] = (
        "CORTEX Password Reset"
    )

    message["From"] = smtp_sender

    message["To"] = user.email

    message.set_content(
        "Use this secure link to reset "
        "your CORTEX password.\n\n"
        f"{reset_url}\n\n"
        "This link expires in 30 minutes."
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=15,
    ) as smtp:

        smtp.starttls()

        smtp.login(
            smtp_username,
            smtp_password,
        )

        smtp.send_message(message)


# ============================================================
# RESET PASSWORD
# ============================================================

def reset_password(
    db: Session,
    token: str,
    new_password: str,
) -> None:

    token_hash = _hash_reset_token(
        token
    )

    user = (
        db.query(User)
        .filter(
            User.reset_token_hash
            == token_hash
        )
        .first()
    )

    if (
        not user
        or not user.reset_token_expires_at
        or user.reset_token_expires_at
        < datetime.utcnow()
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Reset link is invalid or expired."
            ),
        )

    user.password_hash = hash_password(
        new_password
    )

    user.reset_token_hash = None

    user.reset_token_expires_at = None

    db.commit()