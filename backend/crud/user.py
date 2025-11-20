from sqlalchemy.orm import Session
from backend import models
from backend.schemas import user as user_schema
from backend.core.auth.security import get_password_hash, verify_password

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 객체를 조회합니다."""
    return db.query(models.User).filter(models.User.EMAIL == email).first()

def create_user(db: Session, user: user_schema.UserCreate):
    """새로운 사용자를 DB에 생성합니다."""
    hashed_pw = get_password_hash(user.password)
    db_user = models.User(
        EMAIL=user.email,
        PW=hashed_pw,
        NAME=user.name,
        STATUS='A'
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.PW):
        return None
    return user