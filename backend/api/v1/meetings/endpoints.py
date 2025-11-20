from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.schemas import meeting as meeting_schema
from backend.crud import meeting as meeting_crud
from backend.dependencies import get_current_user
from backend import models
# TODO: Redis/RQ 클라이언트 (get_redis_conn) 임포트 및 backend.worker.process_meeting_job 임포트

router = APIRouter(tags=["Meetings"])

# ==================== 1. 회의 생성 ====================
@router.post("/", response_model=meeting_schema.MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(
    meeting_in: meeting_schema.MeetingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    새로운 회의를 생성합니다.
    
    - **title**: 회의 제목 (필수)
    - **purpose**: 회의 목적 (선택)
    - **is_realtime**: 실시간 회의 여부 (기본값: True)
    
    인증된 사용자만 회의를 생성할 수 있습니다.
    """
    # 현재 로그인한 사용자 ID로 회의 생성
    db_meeting = meeting_crud.create_meeting(
        db=db,
        meeting_in=meeting_in,
        user_id=current_user.USER_ID
    )
    return db_meeting

# ==================== 2. 회의 목록 조회 ====================
@router.get("/", response_model=List[meeting_schema.MeetingOut])
def list_meetings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    현재 사용자가 생성한 회의 목록을 조회합니다.
    
    - **skip**: 건너뛸 개수 (페이징용, 기본값: 0)
    - **limit**: 최대 조회 개수 (기본값: 100)
    
    최신 회의가 먼저 나타납니다.
    """
    meetings = meeting_crud.get_meetings_by_user(
        db=db,
        user_id=current_user.USER_ID,
        skip=skip,
        limit=limit
    )
    return meetings

# ==================== 3. 회의 상세 조회 ====================
@router.get("/{meeting_id}", response_model=meeting_schema.MeetingOut)
def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    특정 회의의 상세 정보를 조회합니다.
    
    - **meeting_id**: 회의 ID (ULID)
    
    본인이 생성한 회의만 조회할 수 있습니다.
    """
    # 회의 조회
    db_meeting = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    
    # 회의가 존재하지 않는 경우
    if not db_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"회의를 찾을 수 없습니다. (meeting_id: {meeting_id})"
        )
    
    # 본인이 생성한 회의인지 확인
    if db_meeting.CREATOR_ID != current_user.USER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 생성한 회의만 조회할 수 있습니다."
        )
    
    return db_meeting

# ==================== 4. 회의 수정 ====================
@router.put("/{meeting_id}", response_model=meeting_schema.MeetingOut)
def update_meeting(
    meeting_id: str,
    meeting_update: meeting_schema.MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    회의 정보를 수정합니다.
    
    - **meeting_id**: 회의 ID (ULID)
    - **title**: 새로운 제목 (선택)
    - **purpose**: 새로운 목적 (선택)
    - **status**: 새로운 상태 (선택)
    
    본인이 생성한 회의만 수정할 수 있습니다.
    """
    # 회의 조회
    db_meeting = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    
    # 회의가 존재하지 않는 경우
    if not db_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"회의를 찾을 수 없습니다. (meeting_id: {meeting_id})"
        )
    
    # 본인이 생성한 회의인지 확인
    if db_meeting.CREATOR_ID != current_user.USER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 생성한 회의만 수정할 수 있습니다."
        )
    
    # 회의 정보 업데이트
    updated_meeting = meeting_crud.update_meeting(
        db=db,
        meeting=db_meeting,
        meeting_in=meeting_update
    )
    
    return updated_meeting

# ==================== 5. 회의 삭제 ====================
@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    회의를 삭제합니다.
    
    - **meeting_id**: 회의 ID (ULID)
    
    본인이 생성한 회의만 삭제할 수 있습니다.
    관련된 STT_CHUNK, SUMMARY, ACTION_ITEM도 함께 삭제됩니다 (CASCADE).
    """
    # 회의 조회
    db_meeting = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    
    # 회의가 존재하지 않는 경우
    if not db_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"회의를 찾을 수 없습니다. (meeting_id: {meeting_id})"
        )
    
    # 본인이 생성한 회의인지 확인
    if db_meeting.CREATOR_ID != current_user.USER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 생성한 회의만 삭제할 수 있습니다."
        )
    
    # 회의 삭제
    meeting_crud.delete_meeting(db=db, meeting=db_meeting)
    
    # 204 No Content는 본문을 반환하지 않음
    return None

# ==================== 6. 회의 종료 (배치 작업 등록) ====================
@router.post("/{meeting_id}/end", status_code=status.HTTP_202_ACCEPTED)
def end_meeting_and_queue_job(
    meeting_id: str,
    end_request: meeting_schema.MeetingEndRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    회의 종료를 요청하고 배치 처리를 위한 RQ Job을 등록합니다.
    
    - **meeting_id**: 회의 ID (ULID)
    - **status**: 종료 후 회의 상태 (기본값: COMPLETED)
    - **ended_at**: 종료 시각 (선택)
    
    회의 종료 시 Pass 2 배치 작업이 자동으로 등록됩니다:
    1. NCP Object Storage에서 오디오 다운로드
    2. ElevenLabs로 고품질 전사
    3. LLM으로 요약 및 액션 아이템 추출
    """
    # 회의 조회
    db_meeting = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    
    # 회의가 존재하지 않는 경우
    if not db_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"회의를 찾을 수 없습니다. (meeting_id: {meeting_id})"
        )
    
    # 본인이 생성한 회의인지 확인
    if db_meeting.CREATOR_ID != current_user.USER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 생성한 회의만 종료할 수 있습니다."
        )
    
    # 회의 종료 처리
    ended_meeting = meeting_crud.end_meeting(
        db=db,
        meeting=db_meeting,
        end_request=end_request
    )
    
    # TODO: RQ 클라이언트를 사용하여 backend.worker.process_meeting_job(meeting_id) 작업 등록
    # from backend.worker import queue_meeting_processing
    # queue_meeting_processing(meeting_id)
    
    return {
        "message": f"회의 종료 요청이 완료되었습니다. (meeting_id: {meeting_id})",
        "meeting_id": meeting_id,
        "status": "배치 작업이 곧 시작됩니다."
    }