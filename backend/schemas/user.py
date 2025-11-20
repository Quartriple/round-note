from pydantic import BaseModel, Field
from typing import Optional

# Pydantic Schemas for User/Auth
class UserCreate(BaseModel):
    email: str = Field(..., description="사용자 이메일, 고유해야 함")
    password: str = Field(..., min_length=8, description="사용자 비밀번호")
    name: str = Field(..., description="사용자 이름")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str  # ULID
    email: str
    name: str

    class Config:
        from_attributes = True

# 로그인 폼용 스키마 (FastAPI OAuth2PasswordRequestForm 대체)
class UserLogin(BaseModel):
    email: str
    password: str