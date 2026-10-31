from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone_number: Optional[str] = None
    location: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    preferred_job_location: Optional[str] = None
    preferred_employment_type: Optional[str] = None
    minimum_match_score: Optional[int] = Field(None, ge=0, le=100)


class UserOut(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    location: Optional[str] = None
    minimum_match_score: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
