from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# Pydantic Schemas for Meeting
class MeetingCreate(BaseModel):
    title: str = Field(..., max_length=100)
    is_realtime: bool = Field(True, description="실시간 회의 여부 (Pass 1)")
    # TODO: 참여자(participants) 목록 필드 추가 고려

class MeetingOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    status: str = Field(..., description="회의 상태 (예: ONGOING, PENDING, COMPLETED)")
    audio_storage_path: Optional[str] = None

    class Config:
        from_attributes = True
        
# TODO: (팀원 C) 회의 종료 요청 스키마 (MeetingEndRequest) 정의