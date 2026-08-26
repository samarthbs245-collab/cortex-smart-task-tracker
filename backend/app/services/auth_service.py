import hashlib
import os
import secrets

import resend

from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from dotenv import load_dotenv
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from werkzeug.security import check_password_hash

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
# PASSWORD HASHER
# ============================================================

password_hasher = PasswordHasher()


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(
    password: str,
) -> str:
    """
    Hash new passwords using Argon2id.
    """
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> tuple[bool, bool]:
    """
    Returns:

        (is_valid, needs_upgrade)

    Argon2 hash:
        (True/False, False)

    Legacy Werkzeug hash:
        (True/False, True)
    """

    # --------------------------------------------------------
    # ARGON2
    # --------------------------------------------------------

    if password_hash.startswith("$argon2"):

        try:
            valid = password_hasher.verify(
                password_hash,
                password,
            )

            needs_upgrade = (
                password_hasher.check_needs_rehash(
                    password_hash
                )
            )

            return valid, needs_upgrade

        except (
            VerifyMismatchError,
            VerificationError,
            InvalidHashError,
        ):
            return False, False


    # --------------------------------------------------------
    # LEGACY WERKZEUG
    # --------------------------------------------------------

    try:

        valid = check_password_hash(
            password_hash,
            password,
        )

        return valid, valid

    except Exception:

        return False, False


# ============================================================
# TOKEN HASHING
# ============================================================

def _hash_token(
    token: str,
) -> str:

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# ============================================================
# CREATE PASSWORD RESET TOKEN
# ============================================================

def _create_reset_token(
    user: User,
) -> str:

    raw_token = secrets.token_urlsafe(
        32
    )

    user.reset_token_hash = (
        _hash_token(raw_token)
    )

    user.reset_token_expires_at = (
        datetime.utcnow()
        + timedelta(
            minutes=RESET_TOKEN_MINUTES
        )
    )

    return raw_token


# ============================================================
# SEND EMAIL WITH RESEND
# ============================================================

def _send_email(
    recipient: str,
    subject: str,
    body: str,
) -> None:
    """
    Send a transactional email through the Resend API.

    Required environment variable:
        RESEND_API_KEY

    Optional:
        RESEND_FROM
        Defaults to Resend's onboarding sender for initial testing.
        For sending to users other than the Resend account owner,
        configure and verify your own domain in Resend and set
        RESEND_FROM to an address on that verified domain.
    """

    resend_api_key = os.getenv(
        "RESEND_API_KEY"
    )

    sender = os.getenv(
        "RESEND_FROM",
        "onboarding@resend.dev",
    ).strip()

    if not resend_api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Resend email service is not configured. "
                "Set RESEND_API_KEY in the environment."
            ),
        )

    if not sender:
        raise HTTPException(
            status_code=503,
            detail=(
                "Resend sender is not configured. "
                "Set RESEND_FROM in the environment."
            ),
        )

    # Configure the SDK from the backend environment.
    resend.api_key = resend_api_key

    # Basic HTML version derived from the existing plain-text body.
    # Escape HTML-sensitive characters first, then convert line breaks.
    import html

    html_body = (
        html.escape(body)
        .replace("\r\n", "\n")
        .replace("\n", "<br>\n")
    )

    params = {
        "from": f"CORTEX AI <{sender}>",
        "to": [recipient],
        "subject": subject,
        "text": body,
        "html": f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(subject)}</title>
</head>
<body style="
    margin:0;
    padding:0;
    background:#070b16;
    font-family:Arial,Helvetica,sans-serif;
    color:#e5e7eb;
">
    <div style="
        max-width:600px;
        margin:0 auto;
        padding:32px 20px;
    ">
        <div style="
            background:#101827;
            border:1px solid #26324a;
            border-radius:16px;
            padding:28px;
        ">
            <div style="
                font-size:24px;
                font-weight:700;
                letter-spacing:3px;
                color:#ffffff;
                margin-bottom:18px;
            ">
                CORTEX AI
            </div>

            <div style="
                height:2px;
                width:100%;
                background:linear-gradient(
                    90deg,
                    #8b5cf6,
                    #6366f1,
                    #22d3ee
                );
                margin-bottom:24px;
            "></div>

            <div style="
                font-size:15px;
                line-height:1.75;
                color:#d1d5db;
            ">
                {html_body}
            </div>

            <div style="
                margin-top:28px;
                padding-top:18px;
                border-top:1px solid #26324a;
                font-size:12px;
                line-height:1.6;
                color:#8b98ad;
            ">
                This is an automated message from CORTEX AI.
                If you did not request this email, you can safely ignore it.
            </div>
        </div>
    </div>
</body>
</html>
""",
    }

    try:
        result = resend.Emails.send(
            params
        )

        # The SDK returns the created email record on success.
        # Log only the email id; never log the API key or message body.
        email_id = None

        if isinstance(result, dict):
            data = result.get("data")
            if isinstance(data, dict):
                email_id = data.get("id")

            if not email_id:
                email_id = result.get("id")

        if email_id:
            print(
                f"CORTEX email queued via Resend: {email_id}"
            )

    except Exception as exc:
        print(
            "CORTEX Resend email error:",
            exc,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to send email right now. "
                "Please try again later."
            ),
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
    """Create a new CORTEX account without email verification."""

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
        goal=goal.strip() if goal else None,
        available_hours=available_hours,
        theme="dark",
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

    normalized_email = (
        email.strip().lower()
    )


    user = (
        db.query(User)
        .filter(
            User.email ==
            normalized_email
        )
        .first()
    )


    if not user:

        raise HTTPException(
            status_code=401,
            detail=(
                "Incorrect email or password."
            ),
        )


    # --------------------------------------------------------
    # VERIFY PASSWORD
    # --------------------------------------------------------

    valid, needs_upgrade = (
        verify_password(
            password,
            user.password_hash,
        )
    )


    if not valid:

        raise HTTPException(
            status_code=401,
            detail=(
                "Incorrect email or password."
            ),
        )


    # --------------------------------------------------------
    # UPGRADE LEGACY PASSWORD HASH
    # --------------------------------------------------------

    if needs_upgrade:

        user.password_hash = (
            hash_password(
                password
            )
        )

        db.commit()

        db.refresh(user)


    return user


# ============================================================
# CREATE JWT
# ============================================================

def create_access_token(
    user_id: int,
) -> str:

    expires_at = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            minutes=
            ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )


    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }


    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ============================================================
# REQUEST PASSWORD RESET
# ============================================================

def request_password_reset(
    db: Session,
    email: str,
) -> None:

    normalized_email = (
        email.strip().lower()
    )


    user = (
        db.query(User)
        .filter(
            User.email ==
            normalized_email
        )
        .first()
    )


    # Do not reveal account existence.
    if not user:
        return


    raw_token = _create_reset_token(
        user
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


    email_body = (
        "You requested a password reset "
        "for your CORTEX account.\n\n"
        "Use this secure link:\n\n"
        f"{reset_url}\n\n"
        "This link expires in 30 minutes "
        "and can only be used once."
    )


    _send_email(
        recipient=user.email,
        subject="CORTEX Password Reset",
        body=email_body,
    )


# ============================================================
# RESET PASSWORD
# ============================================================

def reset_password(
    db: Session,
    token: str,
    new_password: str,
) -> None:

    token_hash = _hash_token(
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
        or
        not user.reset_token_expires_at
        or
        user.reset_token_expires_at
        < datetime.utcnow()
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Reset link is invalid or expired."
            ),
        )


    # --------------------------------------------------------
    # SAVE NEW PASSWORD
    # --------------------------------------------------------

    user.password_hash = (
        hash_password(
            new_password
        )
    )


    # --------------------------------------------------------
    # SINGLE-USE TOKEN
    # --------------------------------------------------------

    user.reset_token_hash = None

    user.reset_token_expires_at = None


    db.commit()