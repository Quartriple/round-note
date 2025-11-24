from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import user as user_schema
from backend.crud import user as user_crud
from backend.core.auth import security
from backend import models
from backend.dependencies import get_current_user
from authlib.integrations.starlette_client import OAuth
import os

router = APIRouter()

# OAuth 설정
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.post("/register")
def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    """새로운 사용자를 등록합니다. 회원가입 후 로그인이 필요합니다."""
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
    
    return {
        "message": "회원가입 성공. 로그인해주세요.",
        "user": {
            "id": db_user.USER_ID,
            "email": db_user.EMAIL,
            "name": db_user.NAME
        }
    }

@router.post("/login")
def login_for_access_token(form_data: user_schema.UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    사용자 인증 후 액세스 토큰을 httpOnly Cookie에 설정합니다.
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
    
    # httpOnly Cookie에 토큰 설정
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=is_production,  # 프로덕션에서만 HTTPS 강제, 개발환경에선 HTTP 허용
        samesite="lax",  # CSRF 방어
        max_age=1800  # 30분 (초 단위)
    )
    
    return {
        "message": "로그인 성공",
        "user": {
            "id": user.USER_ID,
            "email": user.EMAIL,
            "name": user.NAME
        }
    }

@router.get("/google/login")
async def google_login(request: Request):
    """Google OAuth 로그인 시작 - Google 로그인 페이지로 리다이렉트"""
    # 요청된 호스트를 기준으로 redirect_uri 결정
    host = request.headers.get('host', '')
    is_local = 'localhost' in host or '127.0.0.1' in host
    
    if is_local:
        redirect_uri = 'http://localhost:8000/api/v1/auth/google/callback'
    else:
        # 배포 환경: 환경 변수 또는 요청 호스트 기반
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', f'https://{host}/api/v1/auth/google/callback')
    
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Google OAuth 콜백 처리 - 사용자 정보 받아서 JWT 발급"""
    try:
        # Google로부터 액세스 토큰 받기
        token = await oauth.google.authorize_access_token(request)
        
        # 사용자 정보 가져오기
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="사용자 정보를 가져올 수 없습니다.")
        
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        
        print(f"[DEBUG] Google 로그인 - Email: {email}, Name: {name}")
        
        # DB에서 사용자 조회
        db_user = user_crud.get_user_by_email(db, email)
        
        if not db_user:
            # 신규 사용자 생성 (Google OAuth는 비밀번호 없음)
            print(f"[DEBUG] 신규 Google 사용자 생성")
            import secrets
            random_password = secrets.token_urlsafe(32)
            db_user = models.User(
                EMAIL=email,
                PW=security.get_password_hash(random_password),  # 랜덤 비밀번호 해싱
                NAME=name,
                STATUS='A'
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            print(f"[DEBUG] 사용자 생성 완료 - USER_ID: {db_user.USER_ID}")
        else:
            print(f"[DEBUG] 기존 사용자 로그인 - USER_ID: {db_user.USER_ID}")
        
        # JWT 토큰 생성
        access_token = security.create_access_token({"sub": db_user.USER_ID, "email": db_user.EMAIL})
        
        # 프론트엔드로 리다이렉트 (토큰을 httpOnly Cookie로 설정)
        # 요청된 호스트를 기준으로 환경 감지
        host = request.headers.get('host', '')
        is_local = 'localhost' in host or '127.0.0.1' in host
        
        if is_local:
            frontend_url = 'http://localhost:3000'
        else:
            # 배포 환경: CORS_ORIGIN 환경 변수 사용
            frontend_url = os.getenv('CORS_ORIGIN', 'https://round-note-web.onrender.com')
        
        # RedirectResponse에 쿠키 설정
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        response = RedirectResponse(url=f"{frontend_url}/main")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_production,  # 프로덕션에서만 HTTPS 강제
            samesite="lax",
            max_age=1800
        )
        return response
        
    except Exception as e:
        print(f"[DEBUG] Google OAuth 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google 로그인 중 오류가 발생했습니다: {str(e)}")

@router.get("/me", response_model=user_schema.UserOut)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보를 반환합니다.
    
    Authorization: Bearer <token> 헤더가 필요합니다.
    """
    return current_user

@router.post("/logout")
def logout(response: Response, current_user: models.User = Depends(get_current_user)):
    """
    사용자 로그아웃 처리 - httpOnly Cookie 삭제
    
    JWT는 stateless하므로 서버에서 토큰을 무효화할 수 없지만,
    쿠키를 삭제하여 클라이언트에서 토큰에 접근할 수 없도록 합니다.
    """
    print(f"[DEBUG] 로그아웃 - USER_ID: {current_user.USER_ID}, Email: {current_user.EMAIL}")
    
    # httpOnly Cookie 삭제
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    
    return {"message": "로그아웃되었습니다."}

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