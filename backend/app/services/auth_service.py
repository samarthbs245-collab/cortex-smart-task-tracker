import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.user import User


# Load environment variables from .env
load_dotenv()


# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not configured in .env")

ALGORITHM = "HS256"

# Token remains valid for 24 hours
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    """
    Convert a plain-text password into a secure password hash.
    """
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Check whether the entered password matches the stored hash.
    """
    return check_password_hash(password_hash, password)


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

    # Normalize email
    normalized_email = email.strip().lower()

    # Check whether email already exists
    existing_user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        age=age,
        goal=goal,
        available_hours=available_hours,
    )

    # Save to database
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

    # Find user by email
    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    # Don't reveal whether email or password was wrong
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    # Verify password
    if not verify_password(
        password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    return user


# ============================================================
# CREATE JWT ACCESS TOKEN
# ============================================================

def create_access_token(user_id: int) -> str:
    """
    Create a JWT token containing the user's ID.
    """

    expiration_time = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration_time,
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return token