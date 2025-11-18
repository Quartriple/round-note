from sqlalchemy.orm import Session
from typing import List, Optional


def create_summary(db: Session, meeting_id: str, summary_content: str, format: str = "markdown"):
    """회의 요약 생성"""
    # TODO: 실제 Summary 모델 추가 후 구현
    pass


def get_summary_by_meeting(db: Session, meeting_id: str) -> Optional[dict]:
    """회의별 요약 조회"""
    # TODO: 실제 구현
    pass


def update_summary(db: Session, meeting_id: str, summary_content: str):
    """요약 업데이트"""
    # TODO: 실제 구현
    pass


def delete_summary(db: Session, meeting_id: str):
    """요약 삭제"""
    # TODO: 실제 구현
    pass
