from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Shared properties ──────────────────────────────────────────────────────────
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None          # "seeker" | "provider"
    bio: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[str] = None        # comma-separated
    experience_years: Optional[int] = None


# ── Request: create a new user ─────────────────────────────────────────────────
class UserCreate(UserBase):
    email: EmailStr
    password: str
    role: str


# ── Request: update an existing user ──────────────────────────────────────────
class UserUpdate(UserBase):
    password: Optional[str] = None


# ── DB-layer schema (includes hashed_password) ────────────────────────────────
class UserInDBBase(UserBase):
    id: Optional[int] = None
    is_partner: bool = False

    class Config:
        orm_mode = True


# ── Public response schema ─────────────────────────────────────────────────────
class User(UserInDBBase):
    pass


# ── Internal schema that includes the hashed password ─────────────────────────
class UserInDB(UserInDBBase):
    hashed_password: str


# ── Token schemas ──────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
