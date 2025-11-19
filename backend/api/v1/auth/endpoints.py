from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import user as user_schema
from backend.crud import user as user_crud
from backend.core.auth import security
from backend import models

router = APIRouter()

@router.post("/register", response_model=user_schema.Token)
def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """새로운 사용자를 등록하고 JWT 토큰을 발급합니다."""
    print(f"[DEBUG] 회원가입 시도 - Email: {user.email}, Name: {user.name}, Password length: {len(user.password)}")
    
    # 이메일 중복 체크
    existing_user = user_crud.get_user_by_email(db, user.email)
    if existing_user:
        print(f"[DEBUG] 이메일 중복 - Email: {user.email}")
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    # 사용자 생성 (비밀번호 해싱 포함)
    print(f"[DEBUG] 사용자 생성 중...")
    db_user = user_crud.create_user(db, user)
    print(f"[DEBUG] 사용자 생성 완료 - USER_ID: {db_user.USER_ID}, Email: {db_user.EMAIL}")

    # JWT 토큰 생성
    token = security.create_access_token({"sub": db_user.USER_ID, "email": db_user.EMAIL})
    print(f"[DEBUG] JWT 토큰 발급 완료")
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=user_schema.Token)
def login_for_access_token(form_data: user_schema.UserLogin, db: Session = Depends(get_db)):
    """
    사용자 인증 후 액세스 토큰을 발급합니다.
    """
    print(f"[DEBUG] 로그인 시도 - Email: {form_data.email}, Password length: {len(form_data.password)}")
    
    # 사용자 조회
    db_user = user_crud.get_user_by_email(db, form_data.email)
    if db_user:
        print(f"[DEBUG] 사용자 찾음 - Email: {db_user.EMAIL}")
        print(f"[DEBUG] DB 해시: {db_user.PW[:20]}...")
        print(f"[DEBUG] 입력 비밀번호: {form_data.password}")
    else:
        print(f"[DEBUG] 사용자를 찾을 수 없음 - Email: {form_data.email}")
    
    user = user_crud.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        print(f"[DEBUG] 인증 실패")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(f"[DEBUG] 인증 성공")
    token = security.create_access_token({"sub": user.USER_ID, "email": user.EMAIL})
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/users/debug")
def get_all_users_debug(db: Session = Depends(get_db)):
    """디버그용: 모든 사용자 조회 (개발 환경에서만 사용, 배포 시 제거 필요)"""
    users = db.query(models.User).all()
    return [
        {
            "user_id": user.USER_ID,
            "email": user.EMAIL,
            "name": user.NAME,
            "status": user.STATUS,
            "join_dt": str(user.JOIN_DT),
            "password_hash_prefix": user.PW[:10] + "..." if user.PW else None  # 해싱 확인용
        }
        for user in users
    ]