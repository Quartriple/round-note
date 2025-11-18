from sqlalchemy.orm import Session
from typing import List, Optional
from backend import models

# [추가] 회의 요약 생성
def create_summary(
    db: Session,
    meeting_id: str,
    summary_content: str,
    format: str = "markdown",
) -> models.Summary:
    """
    회의 요약을 새로 생성합니다.

    - 보통 Pass 2(배치 전사 + LLM 요약) 결과를 DB에 저장할 때 사용합니다.
    - 하나의 회의에 여러 버전의 요약을 남길 수도 있으므로,
      이전 요약이 있어도 새로운 Summary 레코드를 추가합니다.
    """
    summary = models.Summary(
        MEETING_ID=meeting_id,
        CONTENT=summary_content,
        FORMAT=format,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary

# [추가] 회의 요약 조회
def get_summary_by_meeting(
    db: Session,
    meeting_id: str,
) -> Optional[models.Summary]:
    """
    특정 회의의 요약을 조회합니다.

    - 여러 개의 요약이 존재할 수 있다고 가정하고,
      가장 최근 생성된 요약(SUMMARY.CREATED_DT 기준)을 반환합니다.
    """
    return (
        db.query(models.Summary)
        .filter(models.Summary.MEETING_ID == meeting_id)
        .order_by(models.Summary.CREATED_DT.desc())
        .first()
    )

# [추가] 회의 요약 업데이트
def update_summary(
    db: Session,
    meeting_id: str,
    summary_content: str,
    format: Optional[str] = None,
) -> models.Summary:
    """
    기존 회의 요약을 업데이트합니다.

    - 해당 회의에 이미 요약이 있으면 가장 최신 요약을 수정합니다.
    - 요약이 없다면 새로 생성합니다.
    """
    summary = get_summary_by_meeting(db, meeting_id=meeting_id)

    # 기존 요약이 없으면 새로 생성
    if summary is None:
        return create_summary(
            db=db,
            meeting_id=meeting_id,
            summary_content=summary_content,
            format=format or "markdown",
        )

    # 기존 요약이 있으면 내용 업데이트
    summary.CONTENT = summary_content
    if format is not None:
        summary.FORMAT = format

    db.commit()
    db.refresh(summary)
    return summary

# [추가] 회의 요약 삭제
def delete_summary(
    db: Session,
    meeting_id: str,
) -> int:
    """
    특정 회의의 요약을 삭제합니다.

    - 해당 meeting_id에 연결된 모든 요약 레코드를 삭제합니다.
    - 삭제된 행(row) 수를 반환합니다.
    """
    query = db.query(models.Summary).filter(models.Summary.MEETING_ID == meeting_id)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return deleted_count
