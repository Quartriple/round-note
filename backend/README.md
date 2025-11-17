# RoundNote Backend - 개발 가이드

## 목차
- 프로젝트 구조
- 시작하기
- 역할 배분
- API 엔드포인트
- 개발 규칙
- 주요 기능

---

## 프로젝트 구조

```
backend/
├── main.py                   # FastAPI 애플리케이션 엔트리 포인트
├── worker.py                 # RQ Worker 실행 및 Job 정의
├── database.py               # DB 연결 및 세션 관리
├── models.py                 # SQLAlchemy ORM 모델 정의
├── alembic/                  # DB 마이그레이션 도구
│
├── api/
│   └── v1/                   # API 버전 관리
│       ├── __init__.py
│       ├── auth/             # 사용자 인증 라우터 (백엔드 리드)
│       │   └── endpoints.py
│       ├── meetings/         # 회의 관리 CRUD 라우터 (백엔드 리드)
│       │   └── endpoints.py
│       ├── realtime/         # 실시간 WebSocket 라우터 (백엔드 보조)
│       │   └── endpoints.py
│       └── reports/          # 보고서/요약 조회 라우터 (RAG & LangChain)
│           └── endpoints.py
│
├── schemas/                  # Pydantic 스키마 정의 (백엔드 리드)
│   ├── __init__.py
│   ├── user.py               # UserCreate, Token 등 정의
│   ├── meeting.py            # MeetingCreate, MeetingOut 등 정의
│   └── report.py             # ActionItemOut, SummaryOut, ReportOut 등 정의
│
├── crud/                     # 데이터베이스 CRUD 로직
│   ├── __init__.py
│   ├── user.py               # User DB 접근 (백엔드 리드)
│   ├── meeting.py            # Meeting DB 접근 (백엔드 리드)
│   ├── summary.py            # Summary/Report DB 접근 (RAG & LangChain)
│   └── action_item.py        # ActionItem DB 접근 (RAG & LangChain)
│
└── core/                     # 핵심 비즈니스 로직 및 외부 서비스 통합
    ├── auth/                 # JWT/인증 로직 (백엔드 리드)
    │   └── security.py
    ├── llm/                  # LLM/LangChain 파이프라인 (RAG & LangChain)
    │   ├── service.py        # LLM 호출, 프롬프트 관리
    │   ├── chain.py          # LangChain 체인 정의
    │   └── rag/              # RAG 파이프라인
    │       ├── retriever.py  # 문서 검색
    │       └── vectorstore.py # 벡터 저장소 (pgvector)
    ├── stt/                  # STT API 통합 (백엔드 보조)
    │   └── service.py        # Deepgram API 호출
    └── storage/              # NCP Object Storage I/O (백엔드 보조)
        └── service.py        # 오디오 저장 및 다운로드 로직
    └── integrations/         # 외부 서비스 통합 (Jira, Notion 등)
        ├── __init__.py
        ├── jira_service.py   # Jira 이슈 생성/업데이트 로직
        └── notion_service.py # Notion 페이지/데이터 업로드 로직
```

---

## 시작하기

### 1. 환경 설정

```bash
# Python 3.11 설치 (Windows)
winget install Python.Python.3.11

# 프로젝트 루트에서 backend 폴더로 이동
cd backend

# 가상 환경 생성 (Python 3.11)
py -3.11 -m venv .venv

# 가상 환경 활성화
# Windows
. .venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. Docker 환경 설정

```bash
# 프로젝트 루트에서 (round-note/)
cd ..

# Docker Compose 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

### 3. 환경 변수 (간략 목록)

아래 환경 변수를 `.env` 또는 Docker Compose 환경에 설정하세요:

- DATABASE_URL
- REDIS_URL
- OPENAI_API_KEY
- DEEPGRAM_API_KEY
- NCP_ENDPOINT_URL
- NCP_ACCESS_KEY
- NCP_SECRET_KEY
- JIRA_BASE_URL
- JIRA_API_TOKEN
- JIRA_USER_EMAIL
- JIRA_DEFAULT_PROJECT_KEY
- NOTION_API_TOKEN
- NOTION_PARENT_PAGE_ID
- JWT_SECRET_KEY
- JWT_ALGORITHM
- CORS_ORIGIN

### 4. 데이터베이스 마이그레이션

```bash
# Backend 디렉토리에서 마이그레이션 적용
alembic upgrade head

# 마이그레이션 생성 (필요시)
alembic revision --autogenerate -m "description"
```

### 5. 서버 실행

```bash
# 모든 서비스는 Docker Compose로 실행합니다
# 프로젝트 루트에서
cd ..

docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

### 6. Docker 컨테이너 확인

```bash
# PostgreSQL 접속
docker exec -it roundnote-postgres psql -U roundnote -d roundnote

# Redis CLI
docker exec -it roundnote-redis redis-cli

# Backend 로그 확인
docker logs -f roundnote-backend
```

---

## 역할 배분

| 담당 역할 | 주요 책임 | 관련 파일 |
|:---|:---|:---|
| **백엔드 리드** | - API 라우터 설계/구현 (auth, meetings)<br>- 인증 & JWT 토큰 관리<br>- User/Meeting CRUD 함수<br>- Pydantic 스키마 정의<br>- DB 모델 관리 | `api/v1/auth/`, `api/v1/meetings/`<br>`crud/user.py`, `crud/meeting.py`<br>`schemas/`, `core/auth/`<br>`models.py` |
| **RAG & LangChain** | - LLM 요약/분석 파이프라인<br>- RAG 시스템 (문서 검색/인덱싱)<br>- LangChain 체인 설계<br>- 액션 아이템/요약 생성<br>- 보고서 조회 API<br>- Summary/ActionItem CRUD | `core/llm/`, `core/llm/rag/`<br>`api/v1/reports/`<br>`crud/summary.py`<br>`crud/action_item.py`<br>`schemas/report.py` |
| **백엔드 보조** | - 실시간 WebSocket 구현<br>- STT 통합 (Deepgram)<br>- 오디오 저장 (NCP Storage)<br>- 실시간 메시지 처리<br>- 음성 업로드/다운로드 | `api/v1/realtime/`<br>`core/stt/`<br>`core/storage/`<br>`worker.py` |

---

## API 엔드포인트

### 인증 (Auth) - 백엔드 리드
```
POST   /api/v1/auth/register       회원가입
POST   /api/v1/auth/login          로그인
POST   /api/v1/auth/logout         로그아웃
GET    /api/v1/auth/me             현재 사용자 정보
POST   /api/v1/auth/refresh        토큰 갱신
```

### 회의 관리 (Meetings) - 백엔드 리드
```
GET    /api/v1/meetings            회의 목록 조회
POST   /api/v1/meetings            새 회의 생성
GET    /api/v1/meetings/{id}       회의 상세 조회
PUT    /api/v1/meetings/{id}       회의 정보 수정
DELETE /api/v1/meetings/{id}       회의 삭제
```

### 실시간 WebSocket (Realtime) - 백엔드 보조
```
WS     /api/v1/realtime/ws?translate=true&summary=false
```

**WebSocket 메시지 포맷:**

클라이언트 → 서버:
```json
{
  "type": "audio",
  "data": "base64_encoded_audio_chunk"
}
```

서버 → 클라이언트:
```json
{
  "type": "final_transcript",
  "text": "회의 내용...",
  "speaker": "User1",
  "timestamp": 1234567890
}
```

### 보고서/요약 조회 (Reports) - RAG & LangChain
```
GET    /api/v1/reports/{meeting_id}/summary     회의 요약
GET    /api/v1/reports/{meeting_id}/action-items 액션 아이템
GET    /api/v1/reports/{meeting_id}/full        최종 보고서
GET    /api/v1/reports/{meeting_id}/search      RAG 검색
POST   /api/v1/reports/{meeting_id}/regenerate  요약 재생성
```

---

## 개발 규칙

### 1. 파일 네이밍
- 파이썬 모듈: `snake_case` (예: `meeting_service.py`)
- 클래스: `PascalCase` (예: `MeetingService`)
- 함수: `snake_case` (예: `get_meeting()`)

### 2. 코드 구조

**CRUD 함수 (crud/meeting.py) - 백엔드 리드:**
```python
def get_meetings_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    """특정 사용자의 회의 목록을 조회합니다."""
    return db.query(models.Meeting)\
        .filter(models.Meeting.creator_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
```

**API 엔드포인트 (api/v1/meetings/endpoints.py) - 백엔드 리드:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend import crud, schemas
from backend.dependencies import get_db

router = APIRouter(prefix="/meetings", tags=["Meetings"])

@router.get("/")
def list_meetings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """회의 목록 조회"""
    meetings = crud.meeting.get_meetings_by_user(db, user_id, skip, limit)
    return meetings
```

**클래스 기반 서비스와 의존성 주입 패턴 (core/stt/service.py + api/v1/realtime/endpoints.py):**

서비스는 클래스로 구현하고, 각 서비스의 인스턴스를 반환하는 의존성 제공자를 `dependencies.py`에 정의합니다:

```python
# core/stt/service.py
class STTService:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not set")
    
    def get_realtime_stt_url(self):
        return f"wss://api.deepgram.com/v1/listen?language=ko&model=nova-2&diarize=true"
    
    async def transcribe(self, audio_chunk: bytes) -> str:
        # 실제 Deepgram API 호출
        pass
```

```python
# dependencies.py
from backend.core.stt.service import STTService
from backend.core.llm.service import LLMService

def get_stt_service() -> STTService:
    return STTService()

def get_llm_service() -> LLMService:
    return LLMService()
```

엔드포인트에서는 `Depends()` 로 서비스 인스턴스를 주입받습니다:

```python
# api/v1/realtime/endpoints.py
from fastapi import APIRouter, WebSocket, Depends
from backend.dependencies import get_stt_service, get_llm_service
from backend.core.stt.service import STTService
from backend.core.llm.service import LLMService

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    stt_service: STTService = Depends(get_stt_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """실시간 음성 인식 핸들러"""
    await websocket.accept()
    
    # stt_service, llm_service 사용
    url, headers = stt_service.get_realtime_stt_url()
    # ... WebSocket 로직
```

**LLM 요약 함수 (core/llm/service.py) - RAG & LangChain:**
```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from backend.core.llm.rag.retriever import RAGRetriever

async def generate_summary(meeting_id: str, transcript: str):
    """회의 전사본을 요약합니다."""
    retriever = RAGRetriever()
    context = retriever.retrieve(transcript, k=3)
    
    prompt = PromptTemplate.from_template(
        "다음 회의 내용을 요약하세요:\n{context}\n{transcript}"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    summary = chain.run(context=context, transcript=transcript)
    
    return summary
```

**엔드포인트와 서비스 분리 패턴**

API 라우터(`endpoints.py`)는 요청/응답, 권한 체크, HTTP 레이어만 처리하고
핵심 비즈니스 로직은 `service.py`로 분리합니다. `endpoints.py`는 `service.py`의
함수를 호출하여 결과를 반환합니다. 예:

```python
# api/v1/reports/endpoints.py
@router.post("/{meeting_id}/regenerate")
def regenerate_summary(meeting_id: str, db: Session = Depends(get_db)):
    # 입력 검증, 권한 체크
    summary = reports_service.regenerate_summary(meeting_id, db)
    return summary
```

`service.py`는 I/O, 외부 API 호출, RQ 작업 등록 등을 담당합니다.

**WebSocket 핸들러 (api/v1/realtime/endpoints.py) - 백엔드 보조:**
```python
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    translate: bool = False,
    summary: bool = False
):
    """실시간 음성 인식 및 처리"""
    await websocket.accept()
    
    stt_service = STTService()
    
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "audio":
                # 실시간 스트리밍 전사는 UX 목적(부분 자막, 즉각 피드백)에 사용합니다.
                # 전체 오디오에 대한 고품질 전사 및 산출물 생성을 위해
                # 전체 오디오 스트림은 NCP Object Storage에 저장하고
                # 저장된 파일을 배치 방식(예: ElevenLabs API)으로 전송하여
                # 고품질 전사/분석을 수행합니다. 결과물은 DB에 저장되고
                # 필요시 Notion/Jira로 전송됩니다 (core.integrations 사용).
                transcript = await stt_service.transcribe(data["data"])
                await websocket.send_json({
                    "type": "final_transcript",
                    "text": transcript
                })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
```

### 3. 커밋 메시지 컨벤션

형식: `<Type>: <Subject>`

**Type:**
- `Feat:` - 새로운 기능 추가
- `Fix:` - 버그 수정
- `Refactor:` - 코드 리팩토링
- `Style:` - 코드 스타일 변경 (포매팅 등)
- `Test:` - 테스트 코드 추가/수정
- `Docs:` - 문서 수정
- `Chore:` - 빌드, 패키지 매니저 설정

**예시:**
```
Feat: 회의 CRUD 엔드포인트 구현
Feat: RAG 파이프라인 추가
Fix: WebSocket 번역 오류 수정
Docs: README 업데이트
Test: 회의 생성 테스트 추가
```

### 4. 로깅
```python
import logging

logger = logging.getLogger(__name__)

logger.info("회의 생성 시작: %s", meeting_id)
logger.error("LLM 요약 오류: %s", str(e))
```

---

## 주요 기능

### 실시간 음성 인식 (STT) - 백엔드 보조

**흐름:**
1. 프론트엔드에서 오디오 청크 전송 (WebSocket)
2. `core/stt/service.py` → Deepgram API 호출
3. 전사 텍스트 실시간 반환
4. 선택적 번역 (OpenAI API)
5. 오디오 저장 (NCP Object Storage)

**관련 파일:**
- `core/stt/service.py`
- `core/storage/service.py`
- `api/v1/realtime/endpoints.py`
- `worker.py`

### LLM 분석 및 요약 - RAG & LangChain

**흐름:**
1. 전사 완료 후 LLM으로 요약 및 액션 아이템 추출
2. `core/llm/service.py` → LangChain 체인 실행
3. `core/llm/rag/retriever.py` → 유사 문서 검색
4. 결과를 DB에 저장 (crud/summary.py, crud/action_item.py)
5. 최종 보고서 생성

**관련 파일:**
- `core/llm/service.py`
- `core/llm/chain.py`
- `core/llm/rag/retriever.py`
- `core/llm/rag/vectorstore.py`
- `crud/summary.py`
- `crud/action_item.py`
- `api/v1/reports/endpoints.py`

### 저장소 관리 - 백엔드 보조

**기능:**
- 오디오 파일 NCP Object Storage 저장
- 회의 메타데이터 DB 저장
- 실시간 음성 업로드/다운로드

**관련 파일:**
- `core/storage/service.py`
- `api/v1/realtime/endpoints.py`
- `models.py` (Meeting, ArtifactLog)

### RAG 시스템 - RAG & LangChain

**기능:**
- 벡터 임베딩 저장 (pgvector)
- 의미 기반 문서 검색
- 컨텍스트 강화 생성 (RAG)

**관련 파일:**
- `core/llm/rag/vectorstore.py`
- `core/llm/rag/retriever.py`
- `crud/summary.py`

---

## 데이터베이스 스키마

### 핵심 테이블

**USER**
- user_id (PK, ULID)
- email, password_hash, name, phone
- created_at, updated_at, is_active

**MEETING**
- meeting_id (PK, ULID)
- creator_id (FK → USER)
- title, purpose, status (ONGOING/ENDING/COMPLETED)
- start_dt, end_dt
- location (NCP 오디오 경로)

**STT_CHUNK** (실시간 처리 - 백엔드 보조)
- chunk_id (PK, ULID)
- meeting_id (FK)
- start_sec, end_sec
- speaker_label, text
- created_at

**SUMMARY** (요약 - RAG & LangChain)
- summary_id (PK, ULID)
- meeting_id (FK)
- content (JSON/Markdown)
- format (json/markdown)
- created_at

**ACTION_ITEM** (액션 아이템 - RAG & LangChain)
- item_id (PK, ULID)
- meeting_id (FK)
- title, description
- due_date, priority, status
- assignee_id (FK → USER)

**EMBEDDING** (RAG 벡터 - RAG & LangChain)
- embedding_id (PK, ULID)
- meeting_id (FK)
- chunk_text
- embedding (pgvector)
- created_at

---

## 개발 진도 체크리스트 (남은 주요 작업)

- [ ] LangChain + RAG 파이프라인 구현 (`core/llm/chain.py`, `core/llm/rag/`)
- [ ] Reports 서비스 함수 구현 (`get_summary`, `regenerate_summary`, `get_action_items`)
- [ ] Integration tests for Jira/Notion (mocked HTTP)
- [ ] CI / deployment: update Docker Compose and add healthchecks

---

## 주요 환경 변수

| 변수 | 설명 | 예시 |
|:---|:---|:---|
| `DATABASE_URL` | PostgreSQL 연결 문자열 (Docker) | `postgresql://roundnote:password@postgres:5432/roundnote` |
| `REDIS_URL` | Redis 연결 문자열 (Docker) | `redis://redis:6379/0` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-...` |
| `DEEPGRAM_API_KEY` | Deepgram STT API 키 | `...` |
| `NCP_ENDPOINT_URL` | NCP Object Storage 엔드포인트 | `https://...` |
| `JWT_SECRET_KEY` | JWT 서명 키 | `your-secret-key` |
| `JWT_ALGORITHM` | JWT 알고리즘 | `HS256` |
| `CORS_ORIGIN` | CORS 허용 도메인 | `https://roundnote.com` |

---

## 문제 해결

### PostgreSQL 연결 오류
```
ERROR: could not translate host name "postgres" to address
```
**해결:** Docker Compose 서비스 재시작

```bash
docker-compose restart postgres
docker-compose logs postgres
```

### Redis 연결 오류
```
ERROR: ConnectionRefusedError: [Errno 111] Connection refused
```
**해결:** Docker Compose 서비스 재시작

```bash
docker-compose restart redis
docker-compose logs redis
```

### JWT 토큰 검증 오류
```
ERROR: Could not validate credentials
```
**해결:** JWT_SECRET_KEY 확인

```bash
echo %JWT_SECRET_KEY%
```

### Backend 연결 불가
```
ERROR: Connection to backend failed
```
**해결:** Backend 컨테이너 로그 확인

```bash
docker-compose logs -f backend
```

---

## 유용한 명령어

```bash
# FastAPI 자동 문서
http://localhost:8000/docs

# 마이그레이션 상태 확인
alembic current

# 마이그레이션 히스토리
alembic history

# DB 리셋 (개발용)
alembic downgrade base
alembic upgrade head

# PostgreSQL 접속
docker exec -it roundnote-postgres psql -U roundnote -d roundnote

# Redis CLI
docker exec -it roundnote-redis redis-cli

# 컨테이너 로그 확인
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis

# 모든 서비스 중지
docker-compose down

# 모든 서비스 시작
docker-compose up -d
```

---

## 참고 문서

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [LangChain 문서](https://python.langchain.com/docs/)
- [Deepgram 실시간 API](https://developers.deepgram.com/reference/streaming)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Alembic 마이그레이션](https://alembic.sqlalchemy.org/)
- [pgvector 사용 가이드](https://github.com/pgvector/pgvector)

---

## 팀 연락처

| 역할 | 이름 | 담당 업무 |
|:---|:---|:---|
| 팀장 | 권현재 | 프로젝트 총괄 |
| 백엔드 리드 | 김기찬 | User/Meeting CRUD, 인증 시스템 |
| RAG & LangChain | - | LLM 분석, RAG 시스템 |
| 백엔드 보조 | - | STT, WebSocket, 저장소 |

---

**마지막 업데이트:** 2025-11-17  
**버전:** V2.1