from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import meeting as meeting_schema
from backend.crud import meeting as meeting_crud
# TODO: Redis/RQ 클라이언트 (get_redis_conn) 임포트 및 backend.worker.process_meeting_job 임포트

router = APIRouter(prefix="/meetings", tags=["Meetings"])

# TODO: (팀원 A) get_current_user: JWT 토큰으로 현재 사용자 ID를 가져오는 함수 정의

@router.post("/", response_model=meeting_schema.MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(meeting: meeting_schema.MeetingCreate, db: Session = Depends(get_db)):
    """새로운 회의를 생성합니다."""
    # TODO: (팀원 A) 현재 인증된 사용자 ID (user_id) 획득
    # TODO: (팀원 A) meeting_crud.create_meeting(db, meeting, user_id) 호출
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

@router.post("/{meeting_id}/end", status_code=status.HTTP_202_ACCEPTED)
def end_meeting_and_queue_job(meeting_id: int, db: Session = Depends(get_db)):
    """회의 종료를 요청하고 배치 처리를 위한 RQ Job을 등록합니다."""
    # TODO: (팀원 A) meeting_crud를 사용하여 회의 상태를 'ENDING' 또는 'COMPLETED'로 업데이트
    # TODO: (팀원 A) RQ 클라이언트를 사용하여 backend.worker.process_meeting_job(meeting_id) 작업 등록
    return {"message": f"Meeting {meeting_id} end requested. Batch job queued."}

# TODO: (팀원 A) 회의 목록 조회 API 구현 (@router.get("/"))
# TODO: (팀원 A) 회의 상세 조회 API 구현 (@router.get("/{meeting_id}"))