from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.core.storage.service import StorageService
from backend.core.llm.service import LLMService
from backend.core.stt.service import STTService
from backend.core.auth.security import AuthService
from backend.database import get_db

# HTTPBearer: Authorization 헤더에서 Bearer 토큰을 자동으로 추출
security_scheme = HTTPBearer()

def get_storage_service() -> StorageService:
    """StorageService 인스턴스를 생성하고 반환하는 Dependency."""
    return StorageService()

def get_llm_service() -> LLMService:
    """LLMService 인스턴스를 생성하고 반환하는 Dependency."""
    return LLMService()

def get_stt_service() -> STTService:
    """STTService 인스턴스를 생성하고 반환하는 Dependency."""
    return STTService()

def get_auth_service() -> AuthService:
    """AuthService 인스턴스를 생성하고 반환하는 Dependency."""
    return AuthService()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    JWT 토큰을 검증하고 현재 로그인한 사용자를 반환하는 의존성 함수.
    
    Authorization: Bearer <token> 헤더가 필요합니다.
    토큰이 유효하지 않거나 사용자가 존재하지 않으면 401 에러를 반환합니다.
    """
    token = credentials.credentials
    return auth_service.get_current_user(token, db)