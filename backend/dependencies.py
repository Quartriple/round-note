from backend.core.storage.service import StorageService
from backend.core.llm.service import LLMService # LLMService도 포함
from backend.core.stt.service import STTService # STTService도 포함

def get_storage_service() -> StorageService:
    """StorageService 인스턴스를 생성하고 반환하는 Dependency."""
    return StorageService()

def get_llm_service() -> LLMService:
    """LLMService 인스턴스를 생성하고 반환하는 Dependency."""
    return LLMService()

def get_stt_service() -> STTService:
    """STTService 인스턴스를 생성하고 반환하는 Dependency."""
    return STTService()

# TODO: (팀원 C/A) get_db 함수 (데이터베이스 세션) 임포트 및 정의 필요