from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# [추가] 공통으로 쓰는 필드를 한 곳에 모아둔 베이스 클래스
class MeetingBase(BaseModel):
    title: Optional[str] = Field(None, max_length=100, description="회의 제목")
    purpose: Optional[str] = Field(None, max_length=255, description="회의 목적/안건")

# [수정] 회의 생성 요청에 사용할 스키마(POST/meetings)
class MeetingCreate(MeetingBase):
    is_realtime: bool = Field(
        True,
        description="실시간 회의 여부 (Pass 1 WebSocket 사용할지 여부)"
    )
    # TODO: 참여자(participants) 목록 필드 추가 고려

# [추가] 회의 수정 요청에 사용할 스키마 (PUT /meetings/{id})
class MeetingUpdate(MeetingBase):
    status: Optional[str] = Field(
        None,
        description="회의 상태 (예: ONGOING, COMPLETED 등). 필요 시 업데이트"
    )

# [수정] 회의 응답(조회)에 사용할 스키마
class MeetingOut(MeetingBase):
    meeting_id: str = Field(..., description="ULID 기반 회의 ID (TEXT)")
    creator_id: str = Field(..., description="회의 생성한 사용자 ID")
    status: Optional[str] = Field(
        None,
        description="회의 상태 (예: ONGOING, COMPLETED 등)"
    )
    start_dt: datetime = Field(..., description="회의 시작 시각")
    end_dt: Optional[datetime] = Field(
        None,
        description="회의 종료 시각 (아직 안 끝났으면 None)"
    )
    location: Optional[str] = Field(
        None,
        description="회의 오디오 파일이 저장된 NCP Object Storage 경로"
    )

    class Config:
        from_attributes = True  # ORM 객체로부터 바로 변환 가능하도록 설정
        
class MeetingEndRequest(BaseModel):
    """회의 종료 요청 바디 스키마"""

    status: str = Field(
        "COMPLETED",
        description="종료 후 회의 상태 (기본값: COMPLETED)"
    )
    ended_at: Optional[datetime] = Field(
        None,
        description="클라이언트 기준 회의 종료 시각 (보내지 않으면 서버에서 현재 시각 사용)"
    )