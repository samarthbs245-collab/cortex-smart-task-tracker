import re

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# ============================================================
# APPROVED EMAIL DOMAINS
# ============================================================

APPROVED_EMAIL_DOMAINS = {
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "yahoo.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
}


# ============================================================
# EMAIL VALIDATION
# ============================================================

def validate_email_format(
    value: str,
) -> str:

    email = (
        str(value)
        .strip()
        .lower()
    )

    if not email:
        raise ValueError(
            "Email address is required."
        )

    # Spaces are never allowed
    if re.search(r"\s", email):
        raise ValueError(
            "Email address cannot contain spaces."
        )

    # Exactly one @
    if email.count("@") != 1:
        raise ValueError(
            "Enter a valid email address."
        )

    local, domain = email.split("@")

    if not local or not domain:
        raise ValueError(
            "Enter a valid email address."
        )

    # Local part
    if (
        local.startswith(".")
        or local.endswith(".")
        or ".." in local
    ):
        raise ValueError(
            "Enter a valid email address."
        )

    # Domain
    if (
        domain.startswith(".")
        or domain.endswith(".")
        or ".." in domain
    ):
        raise ValueError(
            "Enter a valid email address."
        )

    # Basic characters
    if not re.fullmatch(
        r"[A-Za-z0-9._%+-]+",
        local,
    ):
        raise ValueError(
            "Enter a valid email address."
        )

    if not re.fullmatch(
        r"[A-Za-z0-9.-]+",
        domain,
    ):
        raise ValueError(
            "Enter a valid email address."
        )

    # Must have a normal TLD
    domain_parts = domain.split(".")

    if (
        len(domain_parts) < 2
        or len(domain_parts[-1]) < 2
    ):
        raise ValueError(
            "Enter a valid email address."
        )

    # ========================================================
    # APPROVED PROVIDER CHECK
    # ========================================================

    if domain not in APPROVED_EMAIL_DOMAINS:
        raise ValueError(
            "Please use a supported email provider: "
            "Gmail, Outlook, Yahoo, iCloud or Proton."
        )

    return email


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password_strength(
    password: str,
) -> str:

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    if len(password) > 128:
        raise ValueError(
            "Password cannot exceed 128 characters."
        )

    if not re.search(
        r"[A-Z]",
        password,
    ):
        raise ValueError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(
        r"[a-z]",
        password,
    ):
        raise ValueError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(
        r"\d",
        password,
    ):
        raise ValueError(
            "Password must contain at least one number."
        )

    if not re.search(
        r"[^A-Za-z0-9]",
        password,
    ):
        raise ValueError(
            "Password must contain at least one special character."
        )

    return password


# ============================================================
# USER CREATE
# ============================================================

class UserCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str

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

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Name is required."
            )

        return value

    @field_validator("email")
    @classmethod
    def validate_email(
        cls,
        value: EmailStr,
    ) -> str:

        return validate_email_format(
            str(value)
        )

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str,
    ) -> str:

        return validate_password_strength(
            value
        )


# ============================================================
# USER RESPONSE
# ============================================================

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


# ============================================================
# PROFILE UPDATE
# ============================================================

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

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Name cannot be empty."
            )

        return value


# ============================================================
# LOGIN
# ============================================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str

    @field_validator("email")
    @classmethod
    def validate_login_email(
        cls,
        value: EmailStr,
    ) -> str:

        # Login uses the same approved-provider rule.
        return validate_email_format(
            str(value)
        )


# ============================================================
# TOKEN RESPONSE
# ============================================================

class TokenResponse(BaseModel):

    access_token: str
    token_type: str


# ============================================================
# FORGOT PASSWORD
# ============================================================

class ForgotPasswordRequest(BaseModel):

    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_forgot_email(
        cls,
        value: EmailStr,
    ) -> str:

        return validate_email_format(
            str(value)
        )


# ============================================================
# RESET PASSWORD
# ============================================================

class ResetPasswordRequest(BaseModel):

    token: str = Field(
        min_length=20,
    )

    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(
        cls,
        value: str,
    ) -> str:

        return validate_password_strength(
            value
        )