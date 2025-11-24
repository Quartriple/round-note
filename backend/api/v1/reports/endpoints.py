from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import ulid

from backend.dependencies import get_db
from backend import models
from backend.schemas.report import SummaryOut, ActionItemOut, ReportOut
from backend.core.llm.service import LLMService
from backend.core.integrations import JiraService, NotionService

router = APIRouter(prefix="/reports", tags=["Reports"])

# 외부 연동 서비스
jira = JiraService()
notion = NotionService()


# ============================================
# 1. 회의 요약 조회
# ============================================
@router.get("/{meeting_id}/summary", response_model=SummaryOut)
async def get_meeting_summary(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    회의 요약 조회
    
    프론트엔드에서 사용:
    - 회의 상세 페이지
    - 요약 화면
    """
    
    # 회의 존재 확인
    meeting = db.query(models.Meeting).filter(
        models.Meeting.MEETING_ID == meeting_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting {meeting_id} not found"
        )
    
    # 요약 조회
    summary = db.query(models.Summary).filter(
        models.Summary.MEETING_ID == meeting_id
    ).first()
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary for meeting {meeting_id} not found. Try regenerating the summary."
        )
    
    # Pydantic 모델로 변환 (DB 필드명 → snake_case)
    return SummaryOut(
        summary_id=summary.SUMMARY_ID,
        meeting_id=summary.MEETING_ID,
        format=summary.FORMAT,
        content=summary.CONTENT,
        created_dt=summary.CREATED_DT
    )


# ============================================
# 2. 액션 아이템 목록 조회
# ============================================
@router.get("/{meeting_id}/action-items", response_model=List[ActionItemOut])
async def get_meeting_action_items(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    액션 아이템 목록 조회
    
    프론트엔드에서 사용:
    - 할 일 목록 화면
    - 담당자별 태스크 보드
    """
    
    # 회의 존재 확인
    meeting = db.query(models.Meeting).filter(
        models.Meeting.MEETING_ID == meeting_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting {meeting_id} not found"
        )
    
    # 액션 아이템 조회
    action_items = db.query(models.ActionItem).filter(
        models.ActionItem.MEETING_ID == meeting_id
    ).all()
    
    # Pydantic 모델로 변환
    return [
        ActionItemOut(
            item_id=item.ITEM_ID,
            meeting_id=item.MEETING_ID,
            title=item.TITLE,
            description=item.DESCRIPTION,
            due_dt=item.DUE_DT,
            priority=item.PRIORITY,
            status=item.STATUS,
            assignee_id=item.ASSIGNEE_ID,
            external_tool=item.EXTERNAL_TOOL,
            created_dt=item.CREATED_DT,
            updated_dt=item.UPDATED_DT
        )
        for item in action_items
    ]


# ============================================
# 3. 전체 보고서 조회 (요약 + 액션 아이템)
# ============================================
@router.get("/{meeting_id}/full", response_model=ReportOut)
async def get_full_report(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    전체 보고서 조회 (요약 + 액션 아이템)
    
    프론트엔드에서 사용:
    - 최종 회의록 다운로드
    - 전체 보고서 페이지
    """
    
    # 회의 존재 확인
    meeting = db.query(models.Meeting).filter(
        models.Meeting.MEETING_ID == meeting_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting {meeting_id} not found"
        )
    
    # 요약 조회
    summary = db.query(models.Summary).filter(
        models.Summary.MEETING_ID == meeting_id
    ).first()
    
    # 액션 아이템 조회
    action_items = db.query(models.ActionItem).filter(
        models.ActionItem.MEETING_ID == meeting_id
    ).all()
    
    # Pydantic 모델로 변환
    summary_out = None
    if summary:
        summary_out = SummaryOut(
            summary_id=summary.SUMMARY_ID,
            meeting_id=summary.MEETING_ID,
            format=summary.FORMAT,
            content=summary.CONTENT,
            created_dt=summary.CREATED_DT
        )
    
    action_items_out = [
        ActionItemOut(
            item_id=item.ITEM_ID,
            meeting_id=item.MEETING_ID,
            title=item.TITLE,
            description=item.DESCRIPTION,
            due_dt=item.DUE_DT,
            priority=item.PRIORITY,
            status=item.STATUS,
            assignee_id=item.ASSIGNEE_ID,
            external_tool=item.EXTERNAL_TOOL,
            created_dt=item.CREATED_DT,
            updated_dt=item.UPDATED_DT
        )
        for item in action_items
    ]
    
    # 보고서 조합
    return ReportOut(
        meeting_id=meeting_id,
        summary=summary_out,
        action_items=action_items_out,
        full_transcript=meeting.CONTENT  # 전체 전사 텍스트
    )


# ============================================
# 4. 요약 재생성 (LLM 서비스 사용) ⭐
# ============================================
@router.post("/{meeting_id}/regenerate")
async def regenerate_summary(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """
    회의 요약 재생성 (LLM 활용)
    
    프론트엔드에서 사용:
    - "요약 다시 생성" 버튼
    - 수동 재생성 기능
    
    동작:
    1. Meeting.CONTENT에서 전사 텍스트 가져오기
    2. LLM 서비스로 요약 & 액션 아이템 생성
    3. DB 업데이트
    """
    
    # 회의 존재 확인
    meeting = db.query(models.Meeting).filter(
        models.Meeting.MEETING_ID == meeting_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting {meeting_id} not found"
        )
    
    # 전사 텍스트 확인
    if not meeting.CONTENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transcript found for meeting {meeting_id}. Complete the meeting first."
        )
    
    try:
        # LLM 서비스 초기화
        llm_service = LLMService()
        
        # 전사 텍스트를 리스트로 변환 (청크 단위)
        # CONTENT가 하나의 큰 텍스트라고 가정
        transcript_texts = [meeting.CONTENT]
        
        # LLM으로 요약 및 액션 아이템 생성
        result = await llm_service.get_summary_and_actions(transcript_texts)
        
        # === 요약 업데이트/생성 ===
        summary = db.query(models.Summary).filter(
            models.Summary.MEETING_ID == meeting_id
        ).first()
        
        if summary:
            # 기존 요약 업데이트
            summary.CONTENT = result["rolling_summary"]
            summary.FORMAT = "markdown"
        else:
            # 새 요약 생성
            summary = models.Summary(
                SUMMARY_ID=str(ulid.new()),
                MEETING_ID=meeting_id,
                FORMAT="markdown",
                CONTENT=result["rolling_summary"]
            )
            db.add(summary)
        
        # === 액션 아이템 재생성 ===
        # 기존 액션 아이템 삭제
        db.query(models.ActionItem).filter(
            models.ActionItem.MEETING_ID == meeting_id
        ).delete()
        
        # 새 액션 아이템 생성
        for item_data in result["action_items"]:
            action_item = models.ActionItem(
                ITEM_ID=str(ulid.new()),
                MEETING_ID=meeting_id,
                TITLE=item_data.get("task", ""),
                DESCRIPTION=item_data.get("task", ""),  # task를 description으로도 사용
                STATUS="PENDING",
                PRIORITY="MEDIUM",
                ASSIGNEE_ID=None,  # TODO: 담당자 매핑 필요
                DUE_DT=None  # TODO: deadline 파싱 필요
            )
            db.add(action_item)
        
        # 커밋
        db.commit()
        db.refresh(summary)
        
        return {
            "message": "Summary and action items regenerated successfully",
            "meeting_id": meeting_id,
            "summary": result["rolling_summary"],
            "action_items_count": len(result["action_items"])
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate summary: {str(e)}"
        )


# ============================================
# 5. RAG 검색 (TODO: 권현재님 RAG 완성 후)
# ============================================
@router.get("/{meeting_id}/search")
async def search_meeting_content(
    meeting_id: str,
    query: str,
    db: Session = Depends(get_db)
):
    """
    RAG 기반 회의 내용 검색
    
    TODO: 권현재님의 RAG 시스템 완성 후 구현
    """
    
    return {
        "message": "RAG search not implemented yet",
        "meeting_id": meeting_id,
        "query": query,
        "results": []
    }


# ============================================
# 6. 번역 (요약 또는 전사 내용)
# ============================================
@router.post("/{meeting_id}/translate")
async def translate_meeting_content(
    meeting_id: str,
    content_type: str,  # "summary" or "transcript"
    source_lang: str = "Korean",  # 원문 언어
    target_lang: str = "English",  # 목표 언어
    db: Session = Depends(get_db)
):
    """
    회의 요약 또는 전사 내용을 번역합니다.
    
    - **content_type**: 번역할 내용 타입 ("summary" 또는 "transcript")
    - **source_lang**: 원문 언어 (기본값: "Korean")
    - **target_lang**: 목표 언어 (기본값: "English")
    
    매번 새로 번역하며, DB에는 가장 최근 번역만 캐싱됩니다.
    """
    # 회의 존재 확인
    meeting = db.query(models.Meeting).filter(
        models.Meeting.MEETING_ID == meeting_id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting {meeting_id} not found"
        )
    
    try:
        llm_service = LLMService()
        
        if content_type == "summary":
            # 요약 번역
            summary = db.query(models.Summary).filter(
                models.Summary.MEETING_ID == meeting_id
            ).first()
            
            if not summary:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Summary for meeting {meeting_id} not found"
                )
            
            # 캐시 확인: TRANSLATED_CONTENT에 언어 정보가 포함되어 있는지 확인
            # 형식: "[target_lang]|translated_text"
            cached = False
            if summary.TRANSLATED_CONTENT and summary.TRANSLATED_CONTENT.startswith(f"[{target_lang}]|"):
                # 캐시된 번역 사용
                cached_text = summary.TRANSLATED_CONTENT.split("|", 1)[1]
                return {
                    "meeting_id": meeting_id,
                    "content_type": "summary",
                    "translated_text": cached_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "cached": True
                }
            
            # 캐시에 없으면 새로 번역
            translated_text = await llm_service.get_translation(
                summary.CONTENT,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            # DB에 저장 (언어 정보 포함)
            summary.TRANSLATED_CONTENT = f"[{target_lang}]|{translated_text}"
            db.commit()
            
            return {
                "meeting_id": meeting_id,
                "content_type": "summary",
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "cached": False
            }
        
        elif content_type == "transcript":
            # 전사 내용 번역
            if not meeting.CONTENT:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No transcript found for meeting {meeting_id}"
                )
            
            # 캐시 확인: TRANSLATED_CONTENT에 언어 정보가 포함되어 있는지 확인
            # 형식: "[target_lang]|translated_text"
            if meeting.TRANSLATED_CONTENT and meeting.TRANSLATED_CONTENT.startswith(f"[{target_lang}]|"):
                # 캐시된 번역 사용
                cached_text = meeting.TRANSLATED_CONTENT.split("|", 1)[1]
                return {
                    "meeting_id": meeting_id,
                    "content_type": "transcript",
                    "translated_text": cached_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "cached": True
                }
            
            # 캐시에 없으면 새로 번역
            translated_text = await llm_service.get_translation(
                meeting.CONTENT,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            # DB에 저장 (언어 정보 포함)
            meeting.TRANSLATED_CONTENT = f"[{target_lang}]|{translated_text}"
            db.commit()
            
            return {
                "meeting_id": meeting_id,
                "content_type": "transcript",
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "cached": False
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="content_type must be 'summary' or 'transcript'"
            )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


# ============================================
# 7. Jira 연동 (기존 유지)
# ============================================
@router.post("/{meeting_id}/action-items/to-jira")
async def push_action_items_to_jira(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """액션 아이템을 Jira로 전송"""
    
    action_items = db.query(models.ActionItem).filter(
        models.ActionItem.MEETING_ID == meeting_id
    ).all()
    
    created = []
    for item in action_items:
        resp = jira.create_issue(
            title=item.TITLE,
            description=item.DESCRIPTION or ""
        )
        created.append(resp)
    
    return {"created": created, "count": len(created)}


# ============================================
# 7. Notion 연동 (기존 유지)
# ============================================
@router.post("/{meeting_id}/report/to-notion")
async def push_report_to_notion(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    """전체 보고서를 Notion으로 전송"""
    
    summary = db.query(models.Summary).filter(
        models.Summary.MEETING_ID == meeting_id
    ).first()
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )
    
    blocks = [{
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "text": [{
                "type": "text",
                "text": {"content": summary.CONTENT}
            }]
        }
    }]
    
    resp = notion.create_page(
        title=f"Meeting {meeting_id} Report",
        content_blocks=blocks
    )
    
    return resp


# ============================================
# 8. 테스트용 더미 데이터 생성
# ============================================
@router.post("/dummy/create-sample-data")
async def create_sample_data(db: Session = Depends(get_db)):
    """
    테스트용 더미 회의 데이터 생성
    
    개발/테스트 환경에서만 사용!
    """
    from datetime import datetime
    
    # 더미 회의 생성
    meeting_id = str(ulid.new())
    meeting = models.Meeting(
        MEETING_ID=meeting_id,
        TITLE="샘플 회의 - Q4 프로젝트 진행 상황",
        CONTENT="""
        회의 참석자: 김철수, 이영희, 박민수
        회의 시간: 2024-11-20 14:00
        
        김철수: 백엔드 API 개발이 현재 70% 완료되었습니다.
        이영희: 프론트엔드는 90% 완료되었고, UI/UX 리뷰가 필요합니다.
        박민수: 데이터베이스 마이그레이션은 금요일까지 완료 예정입니다.
        
        결정사항:
        - API 문서 작성 (담당: 김철수, 마감: 11/25)
        - UI 디자인 리뷰 (담당: 이영희, 마감: 11/22)
        - DB 백업 스크립트 작성 (담당: 박민수, 마감: 11/23)
        """,
        START_DT=datetime.now(),
        END_DT=datetime.now(),
        CREATOR_ID="dummy_user_123"
    )
    db.add(meeting)
    
    # 더미 요약 생성
    summary = models.Summary(
        SUMMARY_ID=str(ulid.new()),
        MEETING_ID=meeting_id,
        FORMAT="markdown",
        CONTENT="""## 회의 개요
- Q4 프로젝트 진행 상황 점검
- 참석자: 김철수, 이영희, 박민수

## 핵심 내용
- 백엔드 API 개발 70% 완료
- 프론트엔드 90% 완료
- 데이터베이스 마이그레이션 진행 중

## 다음 단계
- API 문서 작성 (김철수, 11/25)
- UI 디자인 리뷰 (이영희, 11/22)
- DB 백업 스크립트 (박민수, 11/23)"""
    )
    db.add(summary)
    
    # 더미 액션 아이템 생성
    action_items_data = [
        {
            "TITLE": "API 문서 작성 완료",
            "DESCRIPTION": "모든 엔드포인트에 대한 Swagger 문서 작성",
            "PRIORITY": "HIGH",
            "STATUS": "PENDING"
        },
        {
            "TITLE": "UI 디자인 리뷰 진행",
            "DESCRIPTION": "최종 UI/UX 검토 및 피드백 반영",
            "PRIORITY": "MEDIUM",
            "STATUS": "PENDING"
        },
        {
            "TITLE": "DB 백업 스크립트 작성",
            "DESCRIPTION": "자동 백업 스크립트 작성 및 크론잡 설정",
            "PRIORITY": "HIGH",
            "STATUS": "PENDING"
        }
    ]
    
    for item_data in action_items_data:
        action_item = models.ActionItem(
            ITEM_ID=str(ulid.new()),
            MEETING_ID=meeting_id,
            TITLE=item_data["TITLE"],
            DESCRIPTION=item_data["DESCRIPTION"],
            PRIORITY=item_data["PRIORITY"],
            STATUS=item_data["STATUS"]
        )
        db.add(action_item)
    
    db.commit()
    
    return {
        "message": "Sample data created successfully",
        "meeting_id": meeting_id,
        "summary_created": True,
        "action_items_count": len(action_items_data),
        "test_urls": {
            "summary": f"/api/v1/reports/{meeting_id}/summary",
            "action_items": f"/api/v1/reports/{meeting_id}/action-items",
            "full_report": f"/api/v1/reports/{meeting_id}/full",
            "regenerate": f"/api/v1/reports/{meeting_id}/regenerate"
        }
    }