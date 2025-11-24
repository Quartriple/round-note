"""Notion integration service.

회의록을 Notion에 연동하는 서비스.
- 기본 페이지 생성 (기존)
- 포괄적 회의록 생성 (v3 - 멘토 피드백 반영)
- 액션 아이템 DB 추가

환경 변수:
- NOTION_API_TOKEN: Notion Integration Token
- NOTION_PARENT_PAGE_ID: 회의록이 생성될 상위 페이지 ID
- NOTION_DATABASE_ID: 액션 아이템용 Tasks 데이터베이스 ID (선택)

See Notion API docs: https://developers.notion.com/
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import requests


# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class Participant:
    """회의 참석자"""
    user_id: str
    name: str
    role: str  # 'host', 'attendee'


@dataclass
class Discussion:
    """논의 사항"""
    topic: str
    content: str
    speaker: Optional[str] = None


@dataclass
class Decision:
    """결정 사항"""
    content: str
    decided_by: str
    rationale: Optional[str] = None


@dataclass
class PendingIssue:
    """미결 사항"""
    content: str
    reason: str
    next_action: Optional[str] = None


@dataclass
class Attachment:
    """참고 자료"""
    title: str
    url: str
    file_type: str  # 'document', 'spreadsheet', 'presentation', 'link'


# ============================================================
# Notion Service
# ============================================================

class NotionService:
    """Notion 연동 서비스"""
    
    def __init__(self):
        self.api_token = os.getenv("NOTION_API_TOKEN")
        self.parent_page = os.getenv("NOTION_PARENT_PAGE_ID")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    # --------------------------------------------------------
    # 날짜 포맷 헬퍼 (한국어)
    # --------------------------------------------------------
    
    def _format_datetime_kr(self, dt: datetime, end_dt: Optional[datetime] = None) -> str:
        """
        날짜/시간을 한국어 형식으로 변환
        
        결과 예시: 2024년 11월 25일 (월) 14:00 - 15:30
        """
        if not dt:
            return "미정"
            
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일']
        weekday = weekday_kr[dt.weekday()]
        
        # 기본: 2024년 11월 25일 (월) 14:00
        date_str = f"{dt.year}년 {dt.month}월 {dt.day}일 ({weekday}) {dt.strftime('%H:%M')}"
        
        # 종료 시간이 있으면 추가
        if end_dt:
            date_str += f" - {end_dt.strftime('%H:%M')}"
        
        return date_str
    
    def _format_due_date_kr(self, dt: datetime) -> str:
        """
        마감일 형식으로 변환
        
        결과 예시: 11/25 (월)
        """
        if not dt:
            return "미정"
            
        weekday_kr = ['월', '화', '수', '목', '금', '토', '일']
        weekday = weekday_kr[dt.weekday()]
        return f"{dt.month}/{dt.day} ({weekday})"
    
    # --------------------------------------------------------
    # 기존 메서드 (유지)
    # --------------------------------------------------------
    
    def create_page(self, title: str, content_blocks: list) -> dict:
        """Create a Notion page under configured parent page."""
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"page_id": self.parent_page},
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": content_blocks
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def append_blocks(self, block_id: str, blocks: list) -> dict:
        """기존 페이지/블록에 블록 추가"""
        url = f"{self.base_url}/blocks/{block_id}/children"
        resp = requests.patch(url, json={"children": blocks}, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    # --------------------------------------------------------
    # 포괄적 회의록 
    # --------------------------------------------------------
    
    def create_comprehensive_meeting_page(
        self,
        meeting_title: str,
        meeting_date: datetime,
        meeting_end_date: Optional[datetime],
        location: str,
        meeting_type: str,
        participants: List[Participant],  # 필수
        absent_members: List[str],
        purpose: str,
        summary: str,  # 필수
        discussions: List[Discussion],
        decisions: List[Decision],
        action_items: List[Dict],  # 필수
        pending_issues: List[PendingIssue],
        attachments: List[Attachment],
        next_meeting_agenda: Optional[str] = None,
        audio_url: Optional[str] = None,
        transcript_url: Optional[str] = None
    ) -> Dict:
        """
        참석 못한 사람도 완벽히 이해할 수 있는 포괄적인 회의록 페이지 생성
        
        필수 섹션 (무조건 포함):
        1. 참석자
        2. 요약
        3. 액션 아이템
        
        날짜 형식: 2024년 11월 25일 (월) 14:00 - 15:30
        """
        
        # 페이지 제목
        page_title = f"🏢 {meeting_title} - {meeting_date.strftime('%Y-%m-%d')}"
        
        # 날짜/시간 포맷 (한국어)
        date_str = self._format_datetime_kr(meeting_date, meeting_end_date)
        
        # 소요 시간 계산
        if meeting_end_date and meeting_date:
            duration_minutes = int((meeting_end_date - meeting_date).total_seconds() // 60)
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            duration_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"
        else:
            duration_str = "미정"
        
        # 참석자 문자열
        host = next((p.name for p in participants if p.role == 'host'), '')
        attendees = ', '.join([p.name for p in participants]) if participants else "정보 없음"
        
        # 페이지 블록 구성
        children = []
        
        children.append({"type": "divider", "divider": {}})
        
        # ========== 1. 회의 정보 ==========
        children.append(self._heading2("📋 회의 정보", "blue"))
        
        info_items = [
            ("일시", date_str),
            ("소요 시간", duration_str),
            ("장소", location),
            ("회의 유형", meeting_type),
        ]
        
        for key, value in info_items:
            children.append(self._bullet_with_bold_label(key, value))
        
        children.append({"type": "divider", "divider": {}})
        
        # ========== ⭐ 필수 1: 참석자 ==========
        children.append(self._heading2("👥 참석자", "blue"))
        
        if host:
            children.append(self._bullet_with_bold_label("주최", host))
        
        children.append(self._bullet_with_bold_label("참석", attendees))
        
        if absent_members:
            children.append(self._bullet_with_bold_label("불참", ", ".join(absent_members)))
        
        children.append({"type": "divider", "divider": {}})
        
        # ========== ⭐ 필수 2: 요약 ==========
        children.append(self._heading2("📝 요약", "green"))
        children.append(self._paragraph(summary if summary else "요약 없음"))
        children.append({"type": "divider", "divider": {}})
        
        # ========== 3. 회의 목적 (있으면) ==========
        if purpose:
            children.append(self._heading2("🎯 회의 목적", "purple"))
            children.append(self._paragraph(purpose))
            children.append({"type": "divider", "divider": {}})
        
        # ========== 4. 주요 논의사항 (있으면) ==========
        if discussions:
            children.append(self._heading2("💬 주요 논의사항", "green"))
            
            for idx, disc in enumerate(discussions, 1):
                children.append(self._heading3(f"{idx}. {disc.topic}"))
                
                for line in disc.content.split('\n'):
                    if line.strip():
                        children.append(self._bullet(line.strip()))
                
                if disc.speaker:
                    children.append(self._paragraph(f"💬 {disc.speaker} 의견", italic=True))
            
            children.append({"type": "divider", "divider": {}})
        
        # ========== 5. 결정사항 (있으면) ==========
        if decisions:
            children.append(self._heading2("✅ 결정사항", "green"))
            
            for decision in decisions:
                children.append(self._numbered_item(decision.content, bold=True))
                children.append(self._paragraph(f"   👤 결정권자: {decision.decided_by}", italic=True))
                
                if decision.rationale:
                    children.append(self._paragraph(f"   📊 근거: {decision.rationale}", italic=True))
            
            children.append({"type": "divider", "divider": {}})
        
        # ========== ⭐ 필수 3: 액션 아이템 ==========
        children.append(self._heading2("⚡ 액션 아이템", "orange"))
        
        if action_items:
            for item in action_items:
                text = item.get('title', '')
                
                if item.get('assignee'):
                    text += f" (담당: {item['assignee']}"
                    if item.get('due_date'):
                        if isinstance(item['due_date'], datetime):
                            due_str = self._format_due_date_kr(item['due_date'])
                        else:
                            due_str = str(item['due_date'])
                        text += f", 마감: {due_str})"
                    else:
                        text += ")"
                
                children.append(self._todo(text, checked=item.get('status') == 'DONE'))
                
                if item.get('description'):
                    children.append(self._paragraph(f"   ℹ️ {item['description']}", italic=True))
        else:
            children.append(self._paragraph("액션 아이템 없음"))
        
        children.append({"type": "divider", "divider": {}})
        
        # ========== 6. 미결 사항 (있으면) ==========
        if pending_issues:
            children.append(self._heading2("❓ 미결 사항", "yellow"))
            
            for issue in pending_issues:
                children.append(self._numbered_item(issue.content, bold=True))
                children.append(self._paragraph(f"   🔍 보류 이유: {issue.reason}", italic=True))
                
                if issue.next_action:
                    children.append(self._paragraph(f"   ➡️ 다음 조치: {issue.next_action}", italic=True))
            
            children.append({"type": "divider", "divider": {}})
        
        # ========== 7. 참고 자료 (있으면) ==========
        if attachments:
            children.append(self._heading2("📎 참고 자료", "gray"))
            
            type_emoji = {
                'document': '📄',
                'spreadsheet': '📊',
                'presentation': '📽️',
                'link': '🔗'
            }
            
            for att in attachments:
                emoji = type_emoji.get(att.file_type, '📎')
                children.append(self._bullet_with_link(f"{emoji} ", att.title, att.url))
            
            children.append({"type": "divider", "divider": {}})
        
        # ========== 8. 다음 회의 안건 (있으면) ==========
        if next_meeting_agenda:
            children.append(self._heading2("💬 다음 회의 안건", "purple"))
            
            for line in next_meeting_agenda.split('\n'):
                if line.strip():
                    children.append(self._bullet(line.strip()))
            
            children.append({"type": "divider", "divider": {}})
        
        # ========== 9. 회의 기록 ==========
        if audio_url or transcript_url:
            children.append(self._heading2("🎧 회의 기록", "gray"))
            
            if audio_url:
                children.append(self._bullet_with_link("🎙️ ", "회의 녹음 듣기", audio_url))
            
            if transcript_url:
                children.append(self._bullet_with_link("📄 ", "전체 전사 텍스트 보기", transcript_url))
        
        # 페이지 생성
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"page_id": self.parent_page},
            "icon": {"emoji": "📝"},
            "properties": {
                "title": {
                    "title": [{"text": {"content": page_title}}]
                }
            },
            "children": children
        }
        
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        result = resp.json()
        
        return {
            "id": result["id"],
            "url": result["url"],
            "created_time": result["created_time"]
        }
    
    # --------------------------------------------------------
    # 액션 아이템 Tasks DB에 추가
    # --------------------------------------------------------
    
    def create_action_item_in_database(
        self,
        title: str,
        assignee: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: str = "MEDIUM",
        status: str = "PENDING",
        description: Optional[str] = None,
        meeting_title: Optional[str] = None
    ) -> Dict:
        """액션 아이템을 Notion Tasks 데이터베이스에 추가"""
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID가 설정되지 않았습니다")
        
        STATUS_MAPPING = {
            "PENDING": "To Do",
            "TODO": "To Do",
            "IN_PROGRESS": "In Progress",
            "DONE": "Done"
        }
        
        PRIORITY_MAPPING = {
            "HIGH": "High",
            "MEDIUM": "Medium",
            "LOW": "Low"
        }
        
        properties = {
            "Task": {
                "title": [{"text": {"content": title}}]
            },
            "Status": {
                "select": {"name": STATUS_MAPPING.get(status, "To Do")}
            },
            "Priority": {
                "select": {"name": PRIORITY_MAPPING.get(priority, "Medium")}
            }
        }
        
        if assignee:
            properties["Assignee"] = {
                "rich_text": [{"text": {"content": assignee}}]
            }
        
        if due_date:
            properties["Due Date"] = {
                "date": {"start": due_date.strftime("%Y-%m-%d")}
            }
        
        if description:
            properties["Description"] = {
                "rich_text": [{"text": {"content": description}}]
            }
        
        if meeting_title:
            properties["Meeting"] = {
                "rich_text": [{"text": {"content": meeting_title}}]
            }
        
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        resp = requests.post(f"{self.base_url}/pages", json=payload, headers=self.headers)
        resp.raise_for_status()
        result = resp.json()
        
        return {
            "id": result["id"],
            "url": result["url"]
        }
    
    # --------------------------------------------------------
    # 간단한 회의록 (요약 + 액션 아이템만)
    # --------------------------------------------------------
    
    def create_simple_meeting_page(
        self,
        meeting_title: str,
        meeting_date: datetime,
        summary: str,
        action_items: List[Dict]
    ) -> Dict:
        """간단한 회의록 페이지 생성 (요약 + 액션 아이템)"""
        page_title = f"📝 {meeting_title} - {meeting_date.strftime('%Y-%m-%d')}"
        
        children = [
            self._heading2("📋 요약", "blue"),
            self._paragraph(summary),
            {"type": "divider", "divider": {}},
            self._heading2("⚡ 액션 아이템", "orange"),
        ]
        
        for item in action_items:
            text = item.get('title', '')
            if item.get('assignee'):
                text += f" (@{item['assignee']})"
            children.append(self._todo(text, checked=item.get('status') == 'DONE'))
        
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"page_id": self.parent_page},
            "icon": {"emoji": "📝"},
            "properties": {
                "title": {"title": [{"text": {"content": page_title}}]}
            },
            "children": children
        }
        
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        result = resp.json()
        
        return {
            "id": result["id"],
            "url": result["url"]
        }
    
    # --------------------------------------------------------
    # 헬퍼 메서드: Notion 블록 생성
    # --------------------------------------------------------
    
    def _heading2(self, text: str, color: str = "default") -> Dict:
        return {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": text}}],
                "color": color
            }
        }
    
    def _heading3(self, text: str) -> Dict:
        return {
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"text": {"content": text}}]
            }
        }
    
    def _paragraph(self, text: str, italic: bool = False) -> Dict:
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {"content": text},
                    "annotations": {"italic": italic}
                }]
            }
        }
    
    def _bullet(self, text: str) -> Dict:
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": text}}]
            }
        }
    
    def _bullet_with_bold_label(self, label: str, value: str) -> Dict:
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"text": {"content": f"{label}: "}, "annotations": {"bold": True}},
                    {"text": {"content": value}}
                ]
            }
        }
    
    def _bullet_with_link(self, prefix: str, link_text: str, url: str) -> Dict:
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"text": {"content": prefix}},
                    {"text": {"content": link_text, "link": {"url": url}}, "annotations": {"underline": True}}
                ]
            }
        }
    
    def _numbered_item(self, text: str, bold: bool = False) -> Dict:
        return {
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{
                    "text": {"content": text},
                    "annotations": {"bold": bold}
                }]
            }
        }
    
    def _todo(self, text: str, checked: bool = False) -> Dict:
        return {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"text": {"content": text}}],
                "checked": checked
            }
        }
