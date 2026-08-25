from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import *
from app.models.user import User

from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    request_password_reset,
    reset_password,
)

from app.services.auth_dependency import (
    get_current_user,
)


# ============================================================
# AUTH ROUTER
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
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    return create_user(
        db,
        user_data.name,
        user_data.email,
        user_data.password,
        user_data.age,
        user_data.goal,
        user_data.available_hours,
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        login_data.email,
        login_data.password,
    )

    return {
        "access_token": create_access_token(
            user.id
        ),
        "token_type": "bearer",
    }


# ============================================================
# GET CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
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

    for field, value in update_data.items():

        if (
            field == "name"
            and value
        ):
            value = value.strip()

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
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    request_password_reset(
        db,
        payload.email,
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
def do_reset(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset_password(
        db,
        payload.token,
        payload.new_password,
    )

    return {
        "message": (
            "Password reset successful. "
            "You can now sign in."
        )
    }