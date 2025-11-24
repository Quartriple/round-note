# backend/api/v1/chatbot/endpoints.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models
from backend.crud import meeting as meeting_crud
from backend.crud import chatbot as chatbot_crud
from backend.schemas.chatbot import (
    ChatbotQuestionRequest,
    ChatbotAnswerResponse,
    ChatHistoryResponse,
    ChatMessage,
    ChatbotHealthCheck,
)
from backend.core.chatbot.service import ChatbotService

# 🔧 실제 프로젝트의 인증 의존성 위치에 맞게 수정 필요
# 예: from backend.core.auth.dependencies import get_current_user

router = APIRouter()

def get_current_user():
    # 여기서는 그냥 "구현 안 됨" 예외를 던지거나, pass 해도 됨.
    # 테스트에서는 이 함수가 ep.get_current_user = override_get_current_user 로 덮어쓰기된다.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="get_current_user is not implemented",
    )

@router.post(
    "/ask",
    response_model=ChatbotAnswerResponse,
    summary="회의 기반 RAG 챗봇 질의",
)
def ask_chatbot(
    payload: ChatbotQuestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    특정 회의를 컨텍스트로 사용하는 RAG 챗봇 질의 API
    """
    # 1) 회의 존재 여부 검사
    meeting = meeting_crud.get_meeting(db, meeting_id=payload.meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 회의를 찾을 수 없습니다.",
        )

    # (선택) 권한 체크: 회의 생성자/참석자만 접근 허용 등
    # if meeting.CREATOR_ID != current_user.USER_ID:
    #     raise HTTPException(status_code=403, detail="이 회의에 접근 권한이 없습니다.")

    # 2) 서비스 호출
    service = ChatbotService()
    return service.answer_question(
        db=db,
        meeting=meeting,
        user=current_user,
        payload=payload,
    )


@router.get(
    "/{meeting_id}/history",
    response_model=ChatHistoryResponse,
    summary="특정 회의의 챗봇 Q&A 히스토리 조회",
)
def get_chat_history(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    특정 회의에 대해 지금까지 진행된 Q&A 히스토리 조회
    """
    meeting = meeting_crud.get_meeting(db, meeting_id=meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 회의를 찾을 수 없습니다.",
        )

    logs = chatbot_crud.get_chatbot_logs_by_meeting(
        db=db,
        meeting_id=meeting_id,
        limit=100,
    )

    messages: List[ChatMessage] = [
        ChatMessage(
            log_id=log.LOG_ID,
            question=log.Q_TEXT,
            answer=log.A_TEXT,
            asked_dt=log.ASKED_DT,
        )
        for log in logs
    ]

    return ChatHistoryResponse(
        meeting_id=meeting.MEETING_ID,
        meeting_title=meeting.TITLE,
        chat_logs=messages,
    )


@router.get(
    "/health",
    response_model=ChatbotHealthCheck,
    summary="챗봇 / RAG / LLM 헬스 체크",
)
def chatbot_health(
    db: Session = Depends(get_db),
):
    """
    간단한 헬스 체크용 엔드포인트.
    실제로는 vectorstore, OpenAI 호출 등을 테스트하도록 확장할 수 있습니다.
    """
    # TODO: VectorStore, OpenAI ping 등을 실제로 검사하도록 확장 가능
    return ChatbotHealthCheck(
        status="ok",
        rag_enabled=True,
        vectorstore_connected=True,
        llm_available=True,
    )
