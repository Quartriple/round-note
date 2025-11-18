import os
from datetime import datetime, timedelta
from typing import Optional

# 더미 인증 (초기 개발 단계용)
DUMMY_TOKEN = "dummy_token_12345"
DUMMY_USER_ID = "user_12345"
DUMMY_EMAIL = "test@test.com"


def authenticate_dummy():
    """더미 인증 미들웨어 - 실제 JWT 검증은 나중에 구현"""
    return {
        "user_id": DUMMY_USER_ID,
        "email": DUMMY_EMAIL,
        "is_authenticated": True
    }


def create_dummy_token():
    """더미 토큰 생성"""
    return DUMMY_TOKEN


def verify_token(token: str) -> Optional[dict]:
    """토큰 검증 (더미)"""
    if token == DUMMY_TOKEN:
        return authenticate_dummy()
    return None
