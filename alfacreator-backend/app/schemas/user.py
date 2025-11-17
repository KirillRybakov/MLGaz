from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=72)

class User(UserBase):
    id: int
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None

    class Config:
        from_attributes = True
