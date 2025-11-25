from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import user as user_schema
from backend.crud import user as user_crud
from backend.core.auth import security
from backend import models
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

# -------------------------------
# 회원가입
# -------------------------------
@router.post("/register")
def register_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = user_crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    db_user = user_crud.create_user(db, user)
    return {
        "message": "회원가입 성공. 로그인해주세요.",
        "user": {
            "id": db_user.USER_ID,
            "email": db_user.EMAIL,
            "name": db_user.NAME
        }
    }

# -------------------------------
# 로그인
# -------------------------------
@router.post("/login")
def login_for_access_token(form_data: user_schema.UserLogin, response: Response, db: Session = Depends(get_db)):
    user = user_crud.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = security.create_access_token({"sub": user.USER_ID, "email": user.EMAIL})

    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=1800
    )

    return {
        "message": "로그인 성공",
        "user": {
            "id": user.USER_ID,
            "email": user.EMAIL,
            "name": user.NAME
        }
    }

# -------------------------------
# Google OAuth
# -------------------------------
@router.get("/google/login")
async def google_login(request: Request):
    host = request.headers.get('host', '')
    is_local = 'localhost' in host or '127.0.0.1' in host

    if is_local:
        redirect_uri = 'http://localhost:8000/api/v1/auth/google/callback'
    else:
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', f'https://{host}/api/v1/auth/google/callback')

    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="사용자 정보를 가져올 수 없습니다.")

        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])

        db_user = user_crud.get_user_by_email(db, email)
        if not db_user:
            import secrets
            random_password = secrets.token_urlsafe(32)
            db_user = models.User(
                EMAIL=email,
                PW=security.get_password_hash(random_password),
                NAME=name,
                STATUS='A'
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        access_token = security.create_access_token({"sub": db_user.USER_ID, "email": db_user.EMAIL})

        host = request.headers.get('host', '')
        is_local = 'localhost' in host or '127.0.0.1' in host
        frontend_url = 'http://localhost:3000' if is_local else os.getenv('CORS_ORIGIN', 'https://round-note-web.onrender.com')

        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        response = RedirectResponse(url=f"{frontend_url}/main")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_production,
            samesite="lax",
            max_age=1800
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google 로그인 중 오류: {str(e)}")

# -------------------------------
# 현재 사용자 조회 (쿠키 기반 수정)
# -------------------------------
@router.get("/me", response_model=user_schema.UserOut)
def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증 토큰이 없습니다.")

    payload = security.verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰에 사용자 정보가 없습니다.")

    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")

    return user

# -------------------------------
# 로그아웃
# -------------------------------
@router.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증 토큰이 없습니다.")

    payload = security.verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")

    user_id = payload.get("sub")
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")

    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "로그아웃되었습니다."}

# -------------------------------
# 디버그용 사용자 조회
# -------------------------------
@router.get("/users/debug")
def get_all_users_debug(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [
        {
            "user_id": user.USER_ID,
            "email": user.EMAIL,
            "name": user.NAME,
            "status": user.STATUS,
            "join_dt": str(user.JOIN_DT),
            "password_hash_prefix": user.PW[:10] + "..." if user.PW else None
        }
        for user in users
    ]