from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=255, description="Full name of citizen")
    phone: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$", description="10-digit mobile number")
    password: str = Field(..., min_length=8, max_length=128, description="Account password")
    email: Optional[EmailStr] = Field(default=None, description="Optional email address")
    preferred_language: str = Field(default="en", pattern="^(en|hi|mr)$", description="Language preference (en, hi, mr)")

    model_config = ConfigDict(str_strip_whitespace=True)


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$", description="10-digit mobile number")
    password: str = Field(..., min_length=8, max_length=128, description="Account password")

    model_config = ConfigDict(str_strip_whitespace=True)


class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$")
    code: str = Field(..., min_length=4, max_length=6)
    purpose: str = Field(default="register")

    model_config = ConfigDict(str_strip_whitespace=True)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class CitizenProfileResponse(BaseModel):
    id: str
    display_name: str
    phone: str
    email: Optional[str] = None
    preferred_language: str = "en"
    points: int = 0
    is_active: bool = True
    is_verified: bool = False
    role: str = "citizen"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: CitizenProfileResponse
