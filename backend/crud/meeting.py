from sqlalchemy.orm import Session
from backend import models
from backend.schemas import meeting as meeting_schema
from typing import List

def get_meetings_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Meeting]:
    """특정 사용자의 회의 목록을 조회합니다."""
    # TODO: (팀원 C) 사용자 ID를 기준으로 회의 목록 조회 로직 구현
    return db.query(models.Meeting).filter(models.Meeting.owner_id == user_id).offset(skip).limit(limit).all()

def create_meeting(db: Session, meeting: meeting_schema.MeetingCreate, user_id: int) -> models.Meeting:
    """새로운 회의를 DB에 생성합니다."""
    # TODO: (팀원 A) 회의 객체 생성 및 DB 저장 로직 구현
    # db_meeting = models.Meeting(title=meeting.title, is_realtime=meeting.is_realtime, owner_id=user_id, status="ONGOING")
    pass

# TODO: (팀원 A) 회의 상태(status) 업데이트 함수 구현 (예: ENDING, COMPLETED)
# TODO: (팀원 C) 회의 상세 정보 조회 함수 구현