from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional

# [추가] summary 응답 스키마
# DB의 SUMMARY 테이블(models.Summary)에서 가져온 데이터를 클라이언트로 응답할 때 사용하는 JSON 구조
class SummaryOut(BaseModel):
    summary_id: str = Field(..., description="요약 ID (ULID)")
    meeting_id: str = Field(..., description="회의 ID (ULID)")
    format: str = Field(..., description="요약 포맷 (예: markdown, text, json)")
    content: str = Field(..., description="요약 내용")
    created_dt: datetime = Field(..., description="요약 생성 시각")

    class Config:
        from_attributes = True

# [수정] Action Item 응답 스키마
# DB의 ACTION_ITEM 테이블(models.ActionItem)을 조회한 뒤 프론트로 돌려줄 때 사용하는 응답 스키마
class ActionItemOut(BaseModel):
    item_id: str = Field(..., description="액션 아이템 ID (ULID)")
    meeting_id: str = Field(..., description="회의 ID (ULID)")
    title: str = Field(..., description="해야 할 일 제목")
    description: Optional[str] = Field(
        None,
        description="할 일에 대한 상세 설명"
    )
    due_dt: Optional[datetime] = Field(
        None,
        description="마감 기한 (없으면 None)"
    )
    priority: Optional[str] = Field(
        None,
        description="우선순위 (LOW / MEDIUM / HIGH)"
    )
    status: str = Field(
        ...,
        description="상태 (PENDING / IN_PROGRESS / DONE)"
    )
    assignee_id: Optional[str] = Field(
        None,
        description="담당자 USER_ID (없을 수 있음)"
    )
    external_tool: Optional[str] = Field(
        None,
        description="연동된 외부 도구 (예: JIRA, NOTION 등)"
    )
    created_dt: datetime = Field(..., description="액션 아이템 생성 시각")
    updated_dt: Optional[datetime] = Field(
        None,
        description="마지막 수정 시각 (없을 수 있음)"
    )

    class Config:
        from_attributes = True

# [수정] 전체 보고서 응답 스키마 [FinalReportOut 제거]
# 요약 + 액션 아이템을 한 번에 불러오는 Reports API 응답 포맷
class ReportOut(BaseModel):
    """Reports API에서 사용하는 기본 응답 묶음"""

    meeting_id: str = Field(..., description="회의 ID (ULID)")
    summary: Optional[SummaryOut] = Field(
        None,
        description="회의 요약 정보 (없을 수 있음)"
    )
    action_items: List[ActionItemOut] = Field(
        default_factory=list,
        description="회의에서 도출된 액션 아이템 목록"
    )
    full_transcript: Optional[str] = Field(
        None,
        description="필요 시 전체 전사본 텍스트 (옵션)"
    )

# [추가] LLM 응답 포맷(Json schema 초안)
# LLM 프롬프트 설계 & 응답 파싱용 내부 모델 ex) 모델아, 액션 아이템을 이런 JSON 배열 형태로 만들어줘 라고 요구할 때,
# 그 1개 원서의 스키마를 코드로 정의해 둔 것
class LLMActionItemSchema(BaseModel):
    """LLM이 생성하는 액션 아이템 1개의 JSON 포맷 (팀원 B와 협의용)"""

    title: str = Field(..., description="해야 할 일 제목")
    description: Optional[str] = Field(None, description="상세 설명")
    assignee: Optional[str] = Field(
        None,
        description="담당자 이름 또는 식별자 (없을 수 있음)"
    )
    due_date: Optional[date] = Field(
        None,
        description="마감일 (YYYY-MM-DD, 없으면 None)"
    )
    priority: Optional[str] = Field(
        None,
        description="우선순위 (LOW / MEDIUM / HIGH 등)"
    )
    status: Optional[str] = Field(
        None,
        description="상태 (예: PENDING, IN_PROGRESS, DONE)"
    )

# LLM에게 회의 전체 전사 넣어줄게 아래 포맷우로 JSON만 반환해줘 라고 할 때의 전체 결과 포맷
class LLMReportSchema(BaseModel):
    """LLM이 반환하는 전체 보고서 JSON 포맷 (요약 + 액션아이템)"""

    summary: str = Field(..., description="회의 요약 텍스트")
    action_items: List[LLMActionItemSchema] = Field(
        default_factory=list,
        description="LLM이 추출한 액션 아이템 목록"
    )