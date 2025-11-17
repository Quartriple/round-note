from sqlalchemy.orm import Session
from backend import models
from backend.schemas import user as user_schema
# TODO: (팀원 C) 보안 유틸리티 임포트 (예: security.verify_password, security.get_password_hash)

# TODO: (팀원 A/C) 인증/인가에 필요한 유틸리티 함수 정의

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 객체를 조회합니다."""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: user_schema.UserCreate):
    """새로운 사용자를 DB에 생성합니다."""
    # TODO: (팀원 A) 비밀번호 해싱 및 DB 사용자 생성 로직 구현
    # hashed_password = get_password_hash(user.password)
    # db_user = models.User(email=user.email, name=user.name, hashed_password=hashed_password)
    pass