# 🛡️ KoRT: Knights of Round Table (원탁의 기사단)

## 👑 프로젝트 개요: RoundNote (라운드노트)

**RoundNote**는 LLM(대규모 언어 모델)을 기반으로 하는 **실시간 회의 요약 및 액션 아이템 추출 서비스**입니다. 팀원 간의 **공정하고 효율적인 커뮤니케이션(원탁의 정신)**을 보장하고, 논의를 **명확하고 자동화된 실행(액션 아이템)**으로 전환하여 업무 생산성을 극대화하는 것을 목표로 합니다.

*향후 무역 종합상사, 다문화 재판 지원 등 도메인 특화 기능을 추가할 수 있는 확장 가능한 범용적 구조를 구축합니다.*

---

## 📅 프로젝트 기간 및 정보

| 구분 | 내용 |
| :--- | :--- |
| **팀명 (영문)** | **KoRT (Knights of Round Table)** |
| **팀명 (한글)** | **원탁의 기사단** |
| **개발 기간** | 2025.09.26 ~ 2025.12.09 |
| **버전** | V1.0 (Basic Functionality) |

### 👥 팀원 구성

| 역할 (추후 배정) | 이름 | 이메일 |
| :--- | :--- | :--- |
| **팀장** | 권현재 | hyeonjae3575@gmail.com |
| **팀원** | 김기찬 | emyoung611@gmail.com |
| **팀원** | 김선아 | tjsdk101@gmail.com |
| **팀원** | 서동현 | donggus11@gmail.com |
| **팀원** | 정유현 | qoqniard@gmail.com |

---

## 🎯 구현 목표 및 핵심 기능

### 1. 목표 아키텍처 (Initial Pipeline)

회의 음성 입력부터 최종 액션 아이템 출력까지의 전 과정을 Python 기반으로 구현합니다. 

| 단계 | 기술/기능 | 역할 |
| :--- | :--- | :--- |
| **① 입력** | Google Meet 등 미팅 | 회의 데이터 수집 |
| **② 전처리** | Diarization (화자 분리) | 누가 발언했는지 분리 (5명 참여자 기준) |
| **③ 텍스트 변환** | STT (Speech-to-Text) | 각 화자의 음성을 텍스트로 변환 |
| **④ 핵심 처리** | LLM (Large Language Model) | 텍스트를 요약하고 액션 아이템 추출 |
| **⑤ 출력** | Notion 또는 Streamlit 데모 | 회의록, 요약, 액션 아이템 최종 결과물 제공 |

### 2. 핵심 기능

| 기능 | 상세 내용 |
| :--- | :--- |
| **화자별 개별 처리** | 화자별로 STT 결과를 LLM에 개별 전달 후, 다 결합하여 맥락으로 LLM에 다시 인풋을 주는 방식으로 진행 (협의된 구현 의견) |
| **액션 아이템 추출** | '누가, 무엇을, 언제까지 해야 하는지'를 LLM이 정확하게 추출하여 목록화 (예: `비벡:` 액션 아이템 처리) |
| **결과물 제공** | 회의록, 요약, 액션 아이템을 Notion 문서로 생성 및 관리 |

---

## ⚙️ 개발 환경 및 기술 스택

| 분류 | 세부 기술 | 비고/학습 필요 사항 |
| :--- | :--- | :--- |
| **주요 언어** | Python | 프로젝트 전 과정에 사용 |
| **LLM/API** | OpenAI (GPT-4/GPT-5) , Claude | API Key 확보 및 호출 로직 구현 |
| **Diarization** | ElevenLabs API, OpenAI/Gemini | Diarization 개념 및 API 사용법 학습 필수 |
| **STT** | ElevenLabs API, OpenAI/Gemini | STT 개념 학습 필수 |
| **프롬프트** | Prompt Tuning | Prompting Guide 학습 필수 |
| **프레임워크** | Langchain/Langgraph (RAG) | LLM 파이프라인 구축 및 관리 |
| **데모/프론트** | Streamlit | 데모 구현을 위한 학습 필수 |

---

## 🛠️ 향후 역할 배분 및 과제 (To-Do)

### 1. 역할 배분 (확장 가능 구조)

| 담당 역할 (예시) | 팀원 (추후 확정) | 상세 업무 내용 |
| :--- | :--- | :--- |
| **아키텍처/파이프라인 리드** | | 전체 시스템 구조 설계 및 Python 기반 통합 관리 |
| **STT/Diarization 스페셜리스트** | | ElevenLabs API, OpenAI/Gemini 등 활용하여 화자 분리 및 텍스트 변환 정확도 담당 |
| **LLM/Prompt 엔지니어** | | 프롬프트 튜닝, Langchain/Langgraph 활용하여 요약 및 액션 아이템 추출 로직 개발 |
| **데모/프론트엔드 개발** | | Streamlit 데모 구현 및 Notion 연동 담당 |

### 2. 초기 학습 및 필수 과제

모든 팀원은 다음 내용을 학습하고 숙지해야 합니다.

* **Prompt Tuning** 개념 및 활용 (Prompting Guide 참고: [https://www.promptingguide.ai/kr](https://www.promptingguide.ai/kr)) 
* **Streamlit** 데모 구현을 위한 학습 
* **Diarization (화자 분리)** 및 **STT** 개념 및 API 활용법 
* **전 과정 Vibe Coding**을 통해 구현 로직을 완벽히 이해하고 설명 가능하도록 준비 
* **Langchain/Langgraph (RAG)** 학습

---

**원탁의 기사단**은 투명하고 공정한 과정을 통해 최고의 솔루션을 개발합니다. 모든 팀원이 구현 로직을 완벽히 이해하고 협력하여 목표를 달성합시다.