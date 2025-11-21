from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
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
        "status": "배치 작업이 곧 시작됩니다.",
        "content": ended_meeting.CONTENT,
        "audio_url": ended_meeting.AUDIO_URL
    }

# ==================== 7. 회의 오디오 파일 다운로드 ====================
@router.get("/{meeting_id}/audio")
async def get_meeting_audio(
    meeting_id: str,
    token: str = None,  # 쿼리 파라미터로 토큰 전달 가능
    db: Session = Depends(get_db)
):
    """
    회의의 오디오 파일을 다운로드합니다.
    
    - **meeting_id**: 회의 ID (ULID)
    - **token**: JWT 토큰 (쿼리 파라미터로 전달)
    
    본인이 생성한 회의의 오디오 파일만 다운로드할 수 있습니다.
    """
    # 쿼리 파라미터로 전달된 토큰으로 사용자 인증
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다."
        )
    
    try:
        from backend.core.auth.security import verify_token
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰에서 사용자 ID를 찾을 수 없습니다."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"토큰 검증 오류: {str(e)}"
        )
    
    # 회의 조회
    db_meeting = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    
    # 회의가 존재하지 않는 경우
    if not db_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"회의를 찾을 수 없습니다. (meeting_id: {meeting_id})"
        )
    
    # 본인이 생성한 회의인지 확인
    if db_meeting.CREATOR_ID != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 생성한 회의의 오디오만 다운로드할 수 있습니다."
        )
    
    # LOCATION 또는 AUDIO_URL에서 파일 경로 확인
    audio_path = db_meeting.LOCATION or db_meeting.AUDIO_URL
    
    if not audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="오디오 파일이 존재하지 않습니다."
        )
    
    # 로컬 파일 경로 확인 (audio_storage 폴더)
    # Docker 환경에서는 /app/audio_storage, 로컬에서는 ./audio_storage 사용
    base_audio_dir = '/app/audio_storage' if os.path.exists('/app/audio_storage') else './audio_storage'
    
    if audio_path.startswith('./audio_storage/'):
        # 상대 경로를 절대 경로로 변환
        filename = audio_path.replace('./audio_storage/', '')
        file_path = os.path.join(base_audio_dir, filename)
    elif audio_path.startswith('audio_storage/'):
        filename = audio_path.replace('audio_storage/', '')
        file_path = os.path.join(base_audio_dir, filename)
    else:
        # MEETING_ID.wav 형식으로 시도
        file_path = os.path.join(base_audio_dir, f'{meeting_id}.wav')
    
    # 파일 존재 확인
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"오디오 파일을 찾을 수 없습니다: {file_path}"
        )
    
    # 파일 반환
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=f"{db_meeting.TITLE or meeting_id}.wav"
    )


# ==================== 7. 오디오 파일 업로드 ====================
@router.post("/{meeting_id}/audio", status_code=status.HTTP_200_OK)
async def upload_meeting_audio(
    meeting_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    회의 오디오 파일을 업로드합니다.
    
    - **meeting_id**: 회의 ID (필수)
    - **file**: 업로드할 오디오 파일 (필수)
    
    파일은 audio_storage 폴더에 저장되며, DB의 AUDIO_URL과 LOCATION이 자동으로 업데이트됩니다.
    """
    # 1. 회의 존재 여부 확인
    db_meeting = meeting_crud.get_meeting(db, meeting_id=meeting_id)
    if not db_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 회의입니다."
        )
    
    # 2. 권한 확인 (본인이 생성한 회의만 업로드 가능)
    if db_meeting.CREATOR_ID != current_user.USER_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 생성한 회의의 오디오만 업로드할 수 있습니다."
        )
    
    # 3. 파일 저장
    base_audio_dir = '/app/audio_storage' if os.path.exists('/app/audio_storage') else './audio_storage'
    os.makedirs(base_audio_dir, exist_ok=True)
    
    file_path = os.path.join(base_audio_dir, f'{meeting_id}.wav')
    
    try:
        with open(file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 저장 실패: {str(e)}"
        )
    
    # 4. DB 업데이트
    audio_url = f'./audio_storage/{meeting_id}.wav'
    db_meeting.AUDIO_URL = audio_url
    db_meeting.LOCATION = audio_url
    db.commit()
    
    return {
        "message": "오디오 파일이 업로드되었습니다.",
        "audio_url": audio_url,
        "file_size": len(content)
    }