from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

from app.schemas.user import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

from app.security import limiter

from app.services.auth_dependency import (
    get_current_user,
)

from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    request_password_reset,
    reset_password,
)


# ============================================================
# AUTHENTICATION ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    return create_user(
        db=db,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        age=user_data.age,
        goal=user_data.goal,
        available_hours=user_data.available_hours,
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
@limiter.limit("5/minute")
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password,
    )

    return {
        "access_token": create_access_token(
            user.id
        ),
        "token_type": "bearer",
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    return current_user


# ============================================================
# UPDATE PROFILE
# ============================================================

@router.put(
    "/me",
    response_model=UserResponse,
)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    update_data = data.model_dump(
        exclude_unset=True
    )

    if "name" in update_data:
        update_data["name"] = (
            update_data["name"].strip()
        )

    if "goal" in update_data:
        update_data["goal"] = (
            update_data["goal"].strip()
            if update_data["goal"]
            else None
        )

    if "theme" in update_data:
        update_data["theme"] = (
            update_data["theme"]
            .strip()
            .lower()
        )

    for field, value in update_data.items():
        setattr(
            current_user,
            field,
            value,
        )

    db.commit()
    db.refresh(current_user)

    return current_user


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post(
    "/forgot-password",
)
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    request_password_reset(
        db=db,
        email=payload.email,
    )

    return {
        "message": (
            "If an account exists for this email, "
            "reset instructions have been sent."
        )
    }


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post(
    "/reset-password",
)
def do_reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
    )

    return {
        "message": (
            "Password reset successful. "
            "You can now sign in."
        )
    }