from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from backend import models

# [수정] 액션 아이템 생성
# LLM이 뽑아준 액션 아이템을 저장할 때 쓰게 될 함수
def create_action_item(
    db: Session,
    meeting_id: str,
    title: str,
    description: Optional[str] = None,
    priority: str = "MEDIUM",
    due_date: Optional[datetime] = None,
    assignee_id: Optional[str] = None,
    status: str = "PENDING",
    external_tool: Optional[str] = None,
) -> models.ActionItem:
    """
    액션 아이템 생성

    - 보통 LLM이 추출한 액션 아이템을 DB에 저장할 때 호출합니다.
    - 기본 상태는 PENDING, 기본 우선순위는 MEDIUM으로 둡니다.
    """
    item = models.ActionItem(
        MEETING_ID=meeting_id,
        TITLE=title,
        DESCRIPTION=description,
        PRIORITY=priority,
        DUE_DT=due_date,
        ASSIGNEE_ID=assignee_id,
        STATUS=status,
        EXTERNAL_TOOL=external_tool,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# [추가] 회의별 액션 아이템 조회
# 특정 회의(MEETING_ID)에서 나온 모든 액션 아이템을 리스트로 반환
def get_action_items_by_meeting(
    db: Session,
    meeting_id: str,
) -> List[models.ActionItem]:
    """
    회의별 액션 아이템 조회

    - 특정 회의에서 나온 모든 액션 아이템을 반환합니다.
    - 마감일이 있는 항목을 우선 정렬하고, 그 안에서는 마감일 오름차순으로 정렬합니다.
    """
    return (
        db.query(models.ActionItem)
        .filter(models.ActionItem.MEETING_ID == meeting_id)
        .order_by(
            models.ActionItem.DUE_DT.is_(None),  # 마감일 있는 것 먼저
            models.ActionItem.DUE_DT,            # 그 안에서 날짜 순
        )
        .all()
    )

# [추가] 담당자 기준 액션 아잍메 조회
# ASSIGNEE_ID가 특정 사용자(user_id)인 액션 아이템을 전부 가져옴
def get_action_items_by_user(
    db: Session,
    user_id: str,
) -> List[models.ActionItem]:
    """
    담당자 기준 액션 아이템 조회

    - 특정 사용자에게 할당된 모든 액션 아이템을 반환합니다.
    - 마이페이지 '내 할 일' 같은 화면에서 사용할 수 있습니다.
    """
    return (
        db.query(models.ActionItem)
        .filter(models.ActionItem.ASSIGNEE_ID == user_id)
        .order_by(
            models.ActionItem.DUE_DT.is_(None),
            models.ActionItem.DUE_DT,
        )
        .all()
    )

# [추가] 엑션 아이템 업데이트(수정)
# item_id로 객체를 찾고, 전달된 필드들만 선택적으로 업데이트
def update_action_item(
    db: Session,
    item_id: str,
    **kwargs,
) -> Optional[models.ActionItem]:
    """
    액션 아이템 업데이트

    - item_id로 액션 아이템을 찾은 뒤, 전달된 필드들만 선택적으로 업데이트합니다.
    - 예: title, description, priority, status, due_date, assignee_id 등
    """
    item = get_action_item_by_id(db, item_id)
    if item is None:
        return None

    # 허용된 필드만 업데이트 (오타/잘못된 필드 방지용)
    updatable_fields = {
        "title": "TITLE",
        "description": "DESCRIPTION",
        "priority": "PRIORITY",
        "status": "STATUS",
        "due_date": "DUE_DT",
        "assignee_id": "ASSIGNEE_ID",
        "external_tool": "EXTERNAL_TOOL",
    }

    for key, value in kwargs.items():
        if key not in updatable_fields:
            continue
        column_name = updatable_fields[key]
        setattr(item, column_name, value)

    db.commit()
    db.refresh(item)
    return item

# [추가] 액션 아이템 상태 변경
# 상태만 바꾸는 전용 함수 ex) PENDING -> IN_PROGRESS로 바꾸는 UI에 사용가능
def update_action_item_status(
    db: Session,
    item_id: str,
    status: str,
) -> Optional[models.ActionItem]:
    """
    액션 아이템 상태만 간단히 변경 (PENDING / IN_PROGRESS / DONE 등)

    - 자주 사용할 수 있는 패턴이라 별도 헬퍼 함수로 분리했습니다.
    """
    return update_action_item(db, item_id, status=status)

# [추가] 액션 아이템 삭제
# item_id로 레코드를 조회하고 없으면 False 반환/있으면 db.delete, db.commit 후 True 반환
def delete_action_item(
    db: Session,
    item_id: str,
) -> bool:
    """
    액션 아이템 삭제

    - item_id에 해당하는 액션 아이템을 삭제하고,
      실제로 삭제가 발생했으면 True, 없으면 False를 반환합니다.
    """
    item = get_action_item_by_id(db, item_id)
    if item is None:
        return False

    db.delete(item)
    db.commit()
    return True

# [추가] 액션 아이템 조회
# ITEM_ID 기준으로 액션 아이템 한 건을 가져옴
def get_action_item_by_id(
    db: Session,
    item_id: str,
) -> Optional[models.ActionItem]:
    """
    액션 아이템 ID(ITEM_ID)로 단일 액션 아이템 조회
    """
    return (
        db.query(models.ActionItem)
        .filter(models.ActionItem.ITEM_ID == item_id)
        .first()
    )
