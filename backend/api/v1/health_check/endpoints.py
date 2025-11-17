from fastapi import APIRouter
from backend.core.health_check import service as health_service

router = APIRouter(prefix="", tags=["Health"])

@router.get("/")
def health_check():
    """모든 주요 백엔드 서비스의 상태를 확인합니다."""
    return health_service.run_full_health_check()