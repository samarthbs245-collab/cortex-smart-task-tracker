from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    age: int = Field(
        ge=13,
        le=120,
    )

    goal: str | None = Field(
        default=None,
        max_length=100,
    )

    available_hours: float | None = Field(
        default=None,
        ge=0,
        le=24,
    )


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int
    goal: str | None
    available_hours: float | None
    theme: str
    avatar_url: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    age: int | None = Field(
        default=None,
        ge=13,
        le=120,
    )

    goal: str | None = Field(
        default=None,
        max_length=100,
    )

    available_hours: float | None = Field(
        default=None,
        ge=0,
        le=24,
    )

    theme: str | None = Field(
        default=None,
        pattern="^(dark|light)$",
    )

    avatar_url: str | None = Field(
        default=None,
        max_length=500,
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=20,
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )