import ulid
from functools import partial
from sqlalchemy import (
    Column, ForeignKey, TEXT, Float,
    CheckConstraint, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import (
    JSONB
)
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector


# --- Base 및 ULID 기본값 설정 ---

# 모든 모델이 상속할 기본 Base 클래스
Base = declarative_base()

# PK 기본값으로 ULID를 생성하는 헬퍼 함수
def default_ulid():
    return str(ulid.new())

# partial 함수를 사용하여 Column(default=...)에서 직접 호출 가능하도록 함
p_ulid = partial(default_ulid)


# --- 테이블 모델 정의 (11개) ---

# 1. 사용자 (USER는 SQL 예약어이므로 따옴표로 감쌉니다)
class User(Base):
    __tablename__ = '"USER"'
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    USER_ID = Column(TEXT, primary_key=True, default=p_ulid)
    PW = Column(TEXT, nullable=False)
    NAME = Column(TEXT, nullable=False)
    EMAIL = Column(TEXT, unique=True)
    PHONE = Column(TEXT, nullable=True)
    # [수정] DATE -> TIMESTAMP, server_default 사용
    JOIN_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    EXT_API_KEY = Column(TEXT, nullable=True)
    STATUS = Column(TEXT, nullable=False, default='A')
    
    __table_args__ = (
        CheckConstraint(STATUS.in_(['A', 'D']), name='ck_user_status'),
    )

    # [추가코드]
    # === 관계 설정 ===
    meetings = relationship(
        "Meeting",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    action_items = relationship(
        "ActionItem",
        back_populates="assignee",
        cascade="all, delete-orphan"
    )
    knowledge_sources = relationship(
        "KnowledgeSource",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

# 2. 사용자설정
class UserSetting(Base):
    __tablename__ = "USER_SETTING"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    SETTING_ID = Column(TEXT, primary_key=True, default=p_ulid)
    USER_ID = Column(TEXT, ForeignKey('"USER".USER_ID'), nullable=False)
    MEETING_TEMPLATE_ID = Column(TEXT, nullable=True)
    # [수정] Y/N 제약조건 추가
    BOOST_USE_YN = Column(TEXT, nullable=False, default='N')
    
    __table_args__ = (
        CheckConstraint(BOOST_USE_YN.in_(['Y', 'N']), name='ck_user_setting_boost_yn'),
    )

# 3. 회의
class Meeting(Base):
    __tablename__ = "MEETING"
    
    # [수정] PK: VARCHAR2 -> TEXT(ULID)
    MEETING_ID = Column(TEXT, primary_key=True, default=p_ulid)
    # [수정] NN(Not Null) 제약 제거 (Pass 1 수용)
    TITLE = Column(TEXT, nullable=True)
    PURPOSE = Column(TEXT, nullable=True)
    # [수정] DATE -> timestamp, server_default 사용
    START_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    # [수정] NN 제약 제거
    END_DT = Column(TIMESTAMP(timezone=True), nullable=True)
    CREATOR_ID = Column(TEXT, ForeignKey('"USER".USER_ID'), nullable=False)
    # NCP Object Key 저장용
    LOCATION = Column(TEXT, nullable=True)
    
    # [추가 코드]
    # === 관계 설정 ===
    creator = relationship(
        "User",
        back_populates="meetings",
    )
    stt_chunks = relationship(
        "SttChunk",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    summaries = relationship(
        "Summary",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    action_items = relationship(
        "ActionItem",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    chatbot_logs = relationship(
        "ChatbotLog",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    artifact_logs = relationship(
        "ArtifactLog",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    final_analyses = relationship(
        "FinalAnalysis",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )
    embeddings = relationship(
        "Embedding",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )

# 4. 전사 청크
class SttChunk(Base):
    __tablename__ = "STT_CHUNK"
    
    CHUNK_ID = Column(TEXT, primary_key=True, default=p_ulid)
    MEETING_ID = Column(TEXT, ForeignKey("MEETING.MEETING_ID"), nullable=False)
    UTTER_ID = Column(TEXT, nullable=True)
    START_SEC = Column(Float, nullable=False)
    END_SEC = Column(Float, nullable=False)
    SPEAKER_LABEL = Column(TEXT, nullable=True)
    text = Column("TEXT", TEXT, nullable=False)
    # [신규] RAG용 pgvector 컬럼 (OpenAI 임베딩 차원 1536 기준)
    text_vector = Column(Vector(1536), nullable=True)
    CREATED_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # [추가 코드]
    # === 관계 설정 ===
    meeting = relationship(
        "Meeting",
        back_populates="stt_chunks",
    )
    embeddings = relationship(
        "Embedding",
        back_populates="chunk",
        cascade="all, delete-orphan"
    )

# 5. 요약
class Summary(Base):
    __tablename__ = "SUMMARY"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    SUMMARY_ID = Column(TEXT, primary_key=True, default=p_ulid)
    MEETING_ID = Column(TEXT, ForeignKey("MEETING.MEETING_ID"), nullable=False)
    FORMAT = Column(TEXT, nullable=False)
    # [수정] CLOB -> TEXT
    CONTENT = Column(TEXT, nullable=False)
    PROMPT_ID = Column(TEXT, nullable=True)
    CREATED_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # [추가 코드]
    # === 관계 설정 ===
    meeting = relationship(
        "Meeting",
        back_populates="summaries",
    )
    final_analyses = relationship(
        "FinalAnalysis",
        back_populates="summary",
        cascade="all, delete-orphan"
    )

# 6. 액션 아이템
class ActionItem(Base):
    __tablename__ = "ACTION_ITEM"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    ITEM_ID = Column(TEXT, primary_key=True, default=p_ulid)
    MEETING_ID = Column(TEXT, ForeignKey("MEETING.MEETING_ID"), nullable=False)
    TITLE = Column(TEXT, nullable=False)
    # [수정] CLOB -> TEXT
    DESCRIPTION = Column(TEXT, nullable=True)
    DUE_DT = Column(TIMESTAMP(timezone=True), nullable=True)
    PRIORITY = Column(TEXT, nullable=True)
    EXTERNAL_TOOL = Column(TEXT, nullable=True)
    STATUS = Column(TEXT, nullable=False)
    CREATED_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    UPDATED_DT = Column(TIMESTAMP(timezone=True), nullable=True, onupdate=func.now())
    # [추가]
    ASSIGNEE_ID = Column(TEXT, ForeignKey('"USER".USER_ID'), nullable=True)
    # 제약조건 : 상태/우선순위를 정해진 값만 쓰게 하는 코드
    __table_args__ = (
        CheckConstraint(
            STATUS.in_(['PENDING', 'IN_PROGRESS', 'DONE']),
            name='ck_action_item_status'
        ),
        CheckConstraint(
            PRIORITY.in_(['LOW', 'MEDIUM', 'HIGH']),
            name='ck_action_item_priority'
        ),
    )

    # === 관계 설정 ===
    meeting = relationship(
        "Meeting",
        back_populates="action_items",
    )
    assignee = relationship(
        "User",
        back_populates="action_items",
    )

# 7. 회의 챗봇 로그
class ChatbotLog(Base):
    __tablename__ = "CHATBOT_LOG"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    LOG_ID = Column(TEXT, primary_key=True, default=p_ulid)
    MEETING_ID = Column(TEXT, ForeignKey("MEETING.MEETING_ID"), nullable=False)
    USER_ID = Column(TEXT, ForeignKey('"USER".USER_ID'), nullable=False)
    # [수정] CLOB -> TEXT
    Q_TEXT = Column(TEXT, nullable=False)
    A_TEXT = Column(TEXT, nullable=True)
    ASKED_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

# 8. 지식 소스
class KnowledgeSource(Base):
    __tablename__ = "KNOWLEDGE_SOURCE"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    SRC_ID = Column(TEXT, primary_key=True, default=p_ulid)
    OWNER_ID = Column(TEXT, ForeignKey('"USER".USER_ID'), nullable=False)
    SRC_TYPE = Column(TEXT, nullable=False)
    TITLE = Column(TEXT, nullable=True)
    SRC_PATH = Column(TEXT, nullable=True)
    # [수정] CLOB -> JSONB (PostgreSQL의 JSON 타입)
    META_JSON = Column(JSONB, nullable=True)
    # [신규] RAG용 pgvector 컬럼
    content_vector = Column(Vector(1536), nullable=True)
    CREATED_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

# 9. 최종 분석
class FinalAnalysis(Base):
    __tablename__ = "FINAL_ANALYSIS"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    FINAL_ID = Column(TEXT, primary_key=True, default=p_ulid)
    # [수정] 오타 MEEING_ID -> MEETING_ID
    MEETING_ID = Column(TEXT, ForeignKey("MEETING.MEETING_ID"), nullable=False)
    FINAL_TYPE = Column(TEXT, nullable=False)
    # [수정] FK: NUMBER -> TEXT(ULID)
    SUMMARY_ID = Column(TEXT, ForeignKey("SUMMARY.SUMMARY_ID"), nullable=True)
    # [수정] CLOB -> TEXT
    CONTENT = Column(TEXT, nullable=False)
    ARTIFACT_PATH = Column(TEXT, nullable=True)
    CREATED_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

# 10. 키워드 부스팅 사전
class KeywordBoostDict(Base):
    __tablename__ = "KEYWORD_BOOST_DICT"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    KEY_ID = Column(TEXT, primary_key=True, default=p_ulid)
    USER_ID = Column(TEXT, ForeignKey('"USER".USER_ID'), nullable=False)
    KEYWORD = Column(TEXT, nullable=False)
    CATEGORY = Column(TEXT, nullable=True)

# 11. 파일/산출물 로그
class ArtifactLog(Base):
    __tablename__ = "ARTIFACT_LOG"
    
    # [수정] PK: NUMBER -> TEXT(ULID)
    ARTIFACT_LOG_ID = Column(TEXT, primary_key=True, default=p_ulid)
    MEETING_ID = Column(TEXT, ForeignKey("MEETING.MEETING_ID"), nullable=False)
    ARTIFACT_TYPE = Column(TEXT, nullable=False)
    ARTIFACT_PATH = Column(TEXT, nullable=True)
    # [수정] SQL 예약어는 따옴표로 감쌉니다.
    target = Column("TARGET", TEXT, nullable=True)
    result = Column("RESULT", TEXT, nullable=True)
    CREATED_DT = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())