from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.@-]+$")
    email: EmailStr | None = None
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    is_demo_account: bool = False

    @model_validator(mode="after")
    def login_identifier_required(self) -> "UserCreate":
        if not self.username and not self.email:
            raise ValueError("Username or email is required")
        return self


class PublicRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    username: str = Field(..., min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.@-]+$")
    email: EmailStr | None = None
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.@-]+$")
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    is_demo_account: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
