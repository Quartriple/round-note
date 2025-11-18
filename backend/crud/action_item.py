from sqlalchemy.orm import Session
from typing import List, Optional


def create_action_item(
    db: Session,
    meeting_id: str,
    title: str,
    description: Optional[str] = None,
    priority: str = "MEDIUM",
    due_date: Optional[str] = None,
    assignee_id: Optional[str] = None
):
    """액션 아이템 생성"""
    # TODO: 실제 ActionItem 모델 추가 후 구현
    pass


def get_action_items_by_meeting(db: Session, meeting_id: str) -> List[dict]:
    """회의별 액션 아이템 조회"""
    # TODO: 실제 구현
    return []


def update_action_item(db: Session, item_id: str, **kwargs):
    """액션 아이템 업데이트"""
    # TODO: 실제 구현
    pass


def delete_action_item(db: Session, item_id: str):
    """액션 아이템 삭제"""
    # TODO: 실제 구현
    pass


def get_action_item_by_id(db: Session, item_id: str) -> Optional[dict]:
    """액션 아이템 ID로 조회"""
    # TODO: 실제 구현
    pass
