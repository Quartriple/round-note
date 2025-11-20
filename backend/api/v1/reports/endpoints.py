from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.core.llm import service as reports_service
from backend.core.integrations import JiraService, NotionService

router = APIRouter(prefix="/reports", tags=["Reports"])

jira = JiraService()
notion = NotionService()

@router.get("/{meeting_id}/summary")
def get_summary(meeting_id: str, db: Session = Depends(get_db)):
    return reports_service.get_summary(meeting_id, db)

@router.post("/{meeting_id}/regenerate")
def regenerate_summary(meeting_id: str, db: Session = Depends(get_db)):
    # regenerate summary via service layer
    summary = reports_service.regenerate_summary(meeting_id, db)
    return summary

@router.post("/{meeting_id}/action-items/to-jira")
def push_action_items_to_jira(meeting_id: str, db: Session = Depends(get_db)):
    # Example: service returns list of action items
    items = reports_service.get_action_items(meeting_id, db)
    created = []
    for it in items:
        resp = jira.create_issue(title=it.title, description=it.description)
        created.append(resp)
    return {"created": created}

@router.post("/{meeting_id}/report/to-notion")
def push_report_to_notion(meeting_id: str, db: Session = Depends(get_db)):
    summary = reports_service.get_summary(meeting_id, db)
    blocks = [{"object": "block", "type": "paragraph", "paragraph": {"text": [{"type": "text", "text": {"content": summary}}]}}]
    resp = notion.create_page(title=f"Meeting {meeting_id} Report", content_blocks=blocks)
    return resp
