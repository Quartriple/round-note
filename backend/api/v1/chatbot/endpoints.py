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
    FullTextChatbotRequest,
    FullTextChatbotResponse,
)
from backend.core.chatbot.service import ChatbotService

# 🔧 실제 프로젝트의 인증 의존성 위치에 맞게 수정 필요
# 예: from backend.core.auth.dependencies import get_current_user
from backend.dependencies import get_current_user

router = APIRouter()

'''
def get_current_user():
    # 여기서는 그냥 "구현 안 됨" 예외를 던지거나, pass 해도 됨.
    # 테스트에서는 이 함수가 ep.get_current_user = override_get_current_user 로 덮어쓰기된다.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="get_current_user is not implemented",
    )
'''

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
    RAG 챗봇 질의 API
    - meeting_id가 있으면: 특정 회의를 컨텍스트로 사용
    - meeting_id가 없으면: 전체 회의에서 검색
    """
    meeting = None
    
    # 1) meeting_id가 제공된 경우: 회의 존재 여부 검사
    if payload.meeting_id:
        meeting = meeting_crud.get_meeting(db, meeting_id=payload.meeting_id)
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 회의를 찾을 수 없습니다.",
            )
        # (선택) 권한 체크: 회의 생성자/참석자만 접근 허용 등
        # if meeting.CREATOR_ID != current_user.USER_ID:
        #     raise HTTPException(status_code=403, detail="이 회의에 접근 권한이 없습니다.")

    # 2) 서비스 호출 (meeting이 None이면 전체 회의 검색)
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


# ==================== 새로운 원문 기반 챗봇 엔드포인트 ====================

@router.post(
    "/ask-fulltext",
    response_model=FullTextChatbotResponse,
    summary="원문 기반 챗봇 질의 (N개 회의 선택)",
    description=(
        "벡터 검색 없이 N개의 회의 전사 원문을 LLM에 직접 전달하여 질문에 답변합니다. "
        "meeting_ids 리스트로 1개 이상의 회의를 선택할 수 있습니다."
    ),
)
def ask_chatbot_fulltext(
    payload: FullTextChatbotRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    원문 기반 챗봇 질의 API

    - meeting_ids: 질문 대상 회의 ID 리스트 (1개 이상 필수)
    - question: 사용자 질문

    Returns:
        - answer: LLM이 생성한 답변
        - used_meetings: 답변에 사용된 회의 정보 (ID, 제목, 원문 길이)
    """

    # 1) 회의 존재 여부 사전 확인
    meetings = (
        db.query(models.Meeting)
        .filter(models.Meeting.MEETING_ID.in_(payload.meeting_ids))
        .all()
    )

    if not meetings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="요청한 회의를 찾을 수 없습니다.",
        )

    # 요청한 ID와 실제 조회된 ID 비교
    found_ids = {m.MEETING_ID for m in meetings}
    requested_ids = set(payload.meeting_ids)
    missing_ids = requested_ids - found_ids

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"다음 회의를 찾을 수 없습니다: {', '.join(missing_ids)}",
        )

    # (선택) 권한 체크: 회의 생성자/참석자만 접근 허용 등
    # for meeting in meetings:
    #     if meeting.CREATOR_ID != current_user.USER_ID:
    #         raise HTTPException(
    #             status_code=status.HTTP_403_FORBIDDEN,
    #             detail=f"회의 {meeting.MEETING_ID}에 접근 권한이 없습니다."
    #         )

    # 2) 서비스 호출
    try:
        service = ChatbotService()
        return service.answer_question_fulltext(
            db=db,
            payload=payload,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"챗봇 처리 중 오류가 발생했습니다: {str(e)}",
        )
