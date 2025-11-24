# backend/core/chatbot/service.py

import os
from typing import List, Optional

from sqlalchemy.orm import Session
from openai import OpenAI

from backend import models
from backend.crud import chatbot as chatbot_crud
from backend.schemas.chatbot import (
    ChatbotQuestionRequest,
    ChatbotAnswerResponse,
    RetrievedChunk,
)
from backend.core.llm.rag.retriever import RAGRetriever


class ChatbotService:
    """
    회의 기반 RAG 챗봇 서비스 (LangChain 미사용 버전)
    """

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        model: str = "gpt-4.1-mini",
    ):
        """
        Args:
            client: 테스트용 OpenAI 클라이언트 주입 (없으면 환경변수 기반 생성)
            model: 사용할 ChatGPT 계열 모델명
        """
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def _build_meeting_context(self, meeting: models.Meeting) -> dict:
        """
        Meeting 객체에서 프롬프트에 필요한 필드들 추출
        """
        return {
            "title": meeting.TITLE or "",
            "purpose": meeting.PURPOSE or "",
            "summary": meeting.AI_SUMMARY or "",
            "decisions": getattr(meeting, "KEY_DECISIONS", "") or "",
            "next_steps": getattr(meeting, "NEXT_STEPS", "") or "",
        }

    def _invoke_llm(self, system_content: str, user_content: str) -> str:
        """
        OpenAI ChatCompletion 호출 래퍼
        (테스트에서 override 하기 쉽도록 분리)
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content

    def answer_question(
        self,
        db: Session,
        meeting: models.Meeting,
        user: models.User,
        payload: ChatbotQuestionRequest,
    ) -> ChatbotAnswerResponse:
        """
        메인 엔트리: 질문 → (RAG + LLM) → 답변 생성 + 로그 저장
        """

        # 1) 회의 정보 컨텍스트
        ctx = self._build_meeting_context(meeting)

        # 2) 최근 Q&A 컨텍스트 텍스트 생성
        recent_chat_context = chatbot_crud.get_recent_chat_context(
            db, meeting_id=meeting.MEETING_ID, limit=5
        )
        chat_context = (
            recent_chat_context
            if recent_chat_context
            else "이전에 진행된 Q&A가 없습니다."
        )

        # 3) RAG 검색 (필요 시만)
        retrieved_texts: List[str] = []
        if payload.use_rag:
            retriever = RAGRetriever(db)
            # meeting_id로 검색 범위 제한
            retrieved_texts = retriever.retrieve(
                query=payload.question,
                k=5,
                meeting_id=meeting.MEETING_ID,
            )

        rag_context = (
            "\n".join(f"- {t}" for t in retrieved_texts)
            if retrieved_texts
            else "관련 발언이 충분히 검색되지 않았습니다."
        )

        # 4) system / user 프롬프트 구성
        system_prompt = (
            "당신은 회의 내용을 정리해주는 한국어 AI 비서입니다.\n"
            "회의에서 실제로 언급된 내용에 근거해서만 답변하고, "
            "언급되지 않은 내용은 '해당 회의에서 언급되지 않았습니다'라고 명확히 말하세요.\n"
            "답변은 너무 길지 않게, 핵심 위주로 정리해서 설명하세요."
        )

        user_prompt = (
            f"[회의 기본 정보]\n"
            f"- 제목: {ctx['title']}\n"
            f"- 목적: {ctx['purpose']}\n\n"
            f"[회의 요약]\n{ctx['summary']}\n\n"
            f"[주요 결정사항]\n{ctx['decisions']}\n\n"
            f"[다음 단계]\n{ctx['next_steps']}\n\n"
            f"[관련 발언 (RAG 검색 결과)]\n{rag_context}\n\n"
            f"[최근 Q&A]\n{chat_context}\n\n"
            f"[사용자 질문]\n{payload.question}\n\n"
            "위 정보만을 근거로, 한국어로 자연스럽게 답변하세요."
        )

        # 5) LLM 호출
        answer_text = self._invoke_llm(system_prompt, user_prompt)

        # 6) 로그 저장
        log = chatbot_crud.create_chatbot_log(
            db=db,
            meeting_id=meeting.MEETING_ID,
            user_id=user.USER_ID,
            question=payload.question,
            answer=answer_text,
        )

        # 7) 응답 스키마 변환
        retrieved_chunks = (
            [RetrievedChunk(text=t) for t in retrieved_texts]
            if retrieved_texts
            else None
        )

        return ChatbotAnswerResponse(
            log_id=log.LOG_ID,
            question=payload.question,
            answer=answer_text,
            retrieved_chunks=retrieved_chunks,
            confidence=None,  # RAG에서 점수 안 쓰고 있으므로 우선 None
            created_at=log.ASKED_DT,
        )
