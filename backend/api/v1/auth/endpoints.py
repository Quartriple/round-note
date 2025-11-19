from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import user as user_schema
from backend.crud import user as user_crud
from backend.core.auth import security
# TODO: JWT 생성 및 인증 유틸리티 임포트

router = APIRouter()

@router.post("/register", response_model=user_schema.Token)
def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """새로운 사용자를 등록하고 JWT 토큰을 발급합니다."""
    token = security.create_dummy_token()
    return {
        "access_token": token,
        "token_type": "bearer"
    }
    # TODO: user_crud.get_user_by_email을 사용하여 이메일 중복 확인
    # TODO: user_crud.create_user 호출
    # TODO: JWT 토큰 생성 및 user_schema.Token으로 반환 로직 구현

@router.post("/login", response_model=user_schema.Token)
def login_for_access_token(db: Session = Depends(get_db)):
    """사용자 인증 후 액세스 토큰을 발급합니다."""
    
    # TODO: 실제 액세스 토큰 생성 및 반환 로직 구현
    token = security.create_dummy_token()
    return {
        "access_token": token,
        "token_type": "bearer"
    }
    # TODO: (팀원 A) OAuth2PasswordField, 비밀번호 검증 로직 구현