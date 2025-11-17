from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


# Pydantic Schemas for Report/Action Items
class ActionItemOut(BaseModel):
    id: int
    summary: str = Field(..., description="수행해야 할 액션 내용")
    assignee: str = Field(..., description="책임자 이름")
    due_date: Optional[date] = None
    is_completed: bool = False
    
    class Config:
        from_attributes = True

class FinalReportOut(BaseModel):
    meeting_id: int
    full_transcript: str
    summary_text: str
    action_items: List[ActionItemOut]

# TODO: (팀원 B) LLM 응답 포맷을 위한 Json Schema 정의