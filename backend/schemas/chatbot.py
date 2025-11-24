# backend/schemas/chatbot.py

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ChatbotQuestionRequest(BaseModel):
    """
    사용자가 챗봇에게 질의할 때 사용하는 요청 바디
    """
    meeting_id: str = Field(..., description="대상 회의 ID (MEETING_ID)")
    question: str = Field(..., description="사용자 질문")
    use_rag: bool = Field(
        default=True,
        description="RAG(회의 전사 기반 검색)를 사용할지 여부"
    )


class RetrievedChunk(BaseModel):
    """
    RAG로 검색된 텍스트 청크 정보
    (현재는 텍스트만, 필요하면 score 등 추가 가능)
    """
    text: str


class ChatbotAnswerResponse(BaseModel):
    """
    챗봇 답변 응답 스키마
    """
    log_id: str = Field(..., description="CHATBOT_LOG의 PK")
    question: str = Field(..., description="사용자 질문")
    answer: str = Field(..., description="챗봇 답변")
    retrieved_chunks: Optional[List[RetrievedChunk]] = Field(
        default=None,
        description="RAG로 검색된 관련 텍스트 청크들"
    )
    confidence: Optional[float] = Field(
        default=None,
        description="(선택) 답변 신뢰도 점수"
    )
    created_at: datetime = Field(
        ...,
        description="질문/답변 생성 시각 (ASKED_DT)"
    )


class ChatMessage(BaseModel):
    """
    히스토리 조회용 단일 Q&A 메시지
    """
    log_id: str
    question: str
    answer: Optional[str]
    asked_dt: datetime


class ChatHistoryResponse(BaseModel):
    """
    특정 회의에 대한 챗봇 Q&A 히스토리 응답
    """
    meeting_id: str
    meeting_title: Optional[str]
    chat_logs: List[ChatMessage]


class ChatbotHealthCheck(BaseModel):
    """
    챗봇 헬스체크 응답
    """
    status: str
    rag_enabled: bool
    vectorstore_connected: bool
    llm_available: bool
