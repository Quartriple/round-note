from datetime import datetime
from ulid import ULID

DUMMY_USER = {
    "user_id": str(ULID()),
    "email": "test@roundnote.com",
    "name": "테스트 사용자",
    "password_hash": "hashed_password_here"
}

# 권현재와 정유현이 사용할 hardcoded meeting_id
DUMMY_MEETING_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"

DUMMY_MEETING = {
    "meeting_id": DUMMY_MEETING_ID,
    "creator_id": DUMMY_USER["user_id"],
    "title": "Q4 전략 회의",
    "purpose": "분기별 목표 설정",
    "transcript": "안녕하세요. 이번 분기 목표에 대해 논의하겠습니다. 마케팅 팀은 SNS 마케팅을 강화하고, 개발팀은 API 안정성을 개선해야 합니다.",
    "status": "COMPLETED",
    "start_dt": datetime(2025, 11, 17, 10, 0),
    "end_dt": datetime(2025, 11, 17, 11, 30),
    "audio_path": "s3://roundnote/meetings/meeting-123.mp3"
}

DUMMY_ACTION_ITEMS = [
    {
        "item_id": str(ULID()),
        "meeting_id": DUMMY_MEETING_ID,
        "title": "마케팅 계획 수립",
        "description": "Q4 마케팅 전략 수립",
        "assignee_id": DUMMY_USER["user_id"],
        "due_date": datetime(2025, 12, 15),
        "priority": "HIGH",
        "status": "PENDING"
    },
    {
        "item_id": str(ULID()),
        "meeting_id": DUMMY_MEETING_ID,
        "title": "개발 일정 확인",
        "description": "개발팀과 일정 조율",
        "assignee_id": DUMMY_USER["user_id"],
        "due_date": datetime(2025, 12, 20),
        "priority": "MEDIUM",
        "status": "PENDING"
    }
]

DUMMY_SUMMARY = {
    "summary_id": str(ULID()),
    "meeting_id": DUMMY_MEETING_ID,
    "content": "이 회의에서는 Q4 목표를 설정하고 마케팅/개발 전략을 논의했습니다. 주요 액션 아이템은 마케팅 강화와 API 안정성 개선입니다.",
    "format": "markdown",
    "created_at": datetime.now()
}